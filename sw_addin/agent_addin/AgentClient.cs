using System;
using System.IO;
using System.Net.Http;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace agent_addin
{
    internal sealed class AgentClient : IDisposable
    {
        private readonly HttpClient _httpClient;
        private string _sessionId;

        public AgentClient(string serviceBaseUrl)
        {
            ServiceBaseUrl = serviceBaseUrl.TrimEnd('/');
            _httpClient = new HttpClient
            {
                Timeout = Timeout.InfiniteTimeSpan
            };
            _sessionId = Guid.NewGuid().ToString("N");
        }

        public string ServiceBaseUrl { get; private set; }

        public void UpdateBaseUrl(string serviceBaseUrl)
        {
            ServiceBaseUrl = serviceBaseUrl.TrimEnd('/');
        }

        public async Task StreamChatAsync(
            string message,
            Func<string, string, Task> onMessageStart,
            Func<string, Task> onDelta,
            Func<string, string, Task> onAuxiliaryEvent,
            CancellationToken cancellationToken)
        {
            var request = new HttpRequestMessage(HttpMethod.Post, $"{ServiceBaseUrl}/api/chat-sse");
            request.Headers.Accept.ParseAdd("text/event-stream");
            request.Headers.Add("X-Session-Id", _sessionId);
            request.Content = new StringContent(
                "{\"message\":" + ToJsonString(message) + "}",
                Encoding.UTF8,
                "application/json");

            using (var response = await _httpClient.SendAsync(
                request,
                HttpCompletionOption.ResponseHeadersRead,
                cancellationToken))
            {
                response.EnsureSuccessStatusCode();

                if (response.Headers.Contains("X-Session-Id"))
                {
                    _sessionId = string.Join("", response.Headers.GetValues("X-Session-Id"));
                }

                using (var stream = await response.Content.ReadAsStreamAsync())
                using (var reader = new StreamReader(stream, Encoding.UTF8))
                {
                    var eventName = string.Empty;
                    var dataBuilder = new StringBuilder();

                    while (!reader.EndOfStream)
                    {
                        cancellationToken.ThrowIfCancellationRequested();
                        var line = await reader.ReadLineAsync();
                        if (line == null)
                        {
                            break;
                        }

                        if (line.Length == 0)
                        {
                            if (dataBuilder.Length > 0)
                            {
                                var payload = dataBuilder.ToString().TrimEnd('\n');
                                await HandleSsePayload(payload, onMessageStart, onDelta, onAuxiliaryEvent);
                                dataBuilder.Clear();
                                eventName = string.Empty;
                            }

                            continue;
                        }

                        if (line.StartsWith("event:", StringComparison.Ordinal))
                        {
                            eventName = line.Substring("event:".Length).Trim();
                            continue;
                        }

                        if (line.StartsWith("data:", StringComparison.Ordinal))
                        {
                            dataBuilder.Append(line.Substring("data:".Length).TrimStart());
                            dataBuilder.Append('\n');
                        }
                    }

                    if (dataBuilder.Length > 0 && (string.IsNullOrEmpty(eventName) || eventName == "message"))
                    {
                        var payload = dataBuilder.ToString().TrimEnd('\n');
                        await HandleSsePayload(payload, onMessageStart, onDelta, onAuxiliaryEvent);
                    }
                }
            }
        }

        private static async Task HandleSsePayload(
            string payload,
            Func<string, string, Task> onMessageStart,
            Func<string, Task> onDelta,
            Func<string, string, Task> onAuxiliaryEvent)
        {
            var eventType = ExtractJsonString(payload, "type");
            switch (eventType)
            {
                case "message_start":
                    await onMessageStart(
                        ExtractJsonString(payload, "role"),
                        ExtractJsonString(payload, "agent_name"));
                    break;
                case "delta":
                    await onDelta(ExtractJsonString(payload, "content"));
                    break;
                case "status":
                    await onAuxiliaryEvent("status", ExtractJsonString(payload, "message"));
                    break;
                case "execution_log":
                    await onAuxiliaryEvent(
                        ExtractJsonString(payload, "title"),
                        ExtractJsonString(payload, "content"));
                    break;
                case "error":
                    await onAuxiliaryEvent("Error", ExtractJsonString(payload, "error"));
                    break;
                case "done":
                    return;
            }
        }

        private static string ExtractJsonString(string jsonLine, string key)
        {
            var token = $"\"{key}\":";
            var start = jsonLine.IndexOf(token, StringComparison.Ordinal);
            if (start < 0)
            {
                return string.Empty;
            }

            start += token.Length;
            while (start < jsonLine.Length && char.IsWhiteSpace(jsonLine[start]))
            {
                start++;
            }

            if (start >= jsonLine.Length)
            {
                return string.Empty;
            }

            if (jsonLine[start] != '"')
            {
                var endRaw = jsonLine.IndexOfAny(new[] { ',', '}' }, start);
                if (endRaw < 0)
                {
                    endRaw = jsonLine.Length;
                }

                return jsonLine.Substring(start, endRaw - start).Trim();
            }

            start++;
            var builder = new StringBuilder();
            var escaped = false;
            for (var i = start; i < jsonLine.Length; i++)
            {
                var ch = jsonLine[i];
                if (escaped)
                {
                    switch (ch)
                    {
                        case '"':
                        case '\\':
                        case '/':
                            builder.Append(ch);
                            break;
                        case 'n':
                            builder.Append('\n');
                            break;
                        case 'r':
                            builder.Append('\r');
                            break;
                        case 't':
                            builder.Append('\t');
                            break;
                        default:
                            builder.Append(ch);
                            break;
                    }

                    escaped = false;
                    continue;
                }

                if (ch == '\\')
                {
                    escaped = true;
                    continue;
                }

                if (ch == '"')
                {
                    return builder.ToString();
                }

                builder.Append(ch);
            }

            return builder.ToString();
        }

        private static string ToJsonString(string value)
        {
            return "\"" + value
                .Replace("\\", "\\\\")
                .Replace("\"", "\\\"")
                .Replace("\r", "\\r")
                .Replace("\n", "\\n")
                .Replace("\t", "\\t") + "\"";
        }

        public void Dispose()
        {
            _httpClient.Dispose();
        }
    }
}
