using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace agent_addin
{
    [ComVisible(true)]
    [ProgId(AddinConstants.ProgId)]
    [Guid("6D44BF1F-CA09-43D5-8C2F-C9C6B78C8033")]
    [ClassInterface(ClassInterfaceType.None)]
    public class AgentTaskPaneControl : UserControl
    {
        private const int WmSetRedraw = 0x000B;
        private const int StreamFlushIntervalMs = 500;
        private const int StreamFlushThresholdChars = 120;

        [DllImport("user32.dll")]
        private static extern IntPtr SendMessage(IntPtr hWnd, int msg, IntPtr wParam, IntPtr lParam);

        private readonly RichTextBox _conversationBox;
        private readonly TextBox _inputBox;
        private readonly TextBox _serviceUrlBox;
        private readonly Button _sendButton;
        private readonly Button _restartServiceButton;
        private readonly Label _statusLabel;
        private readonly StringBuilder _streamBuffer = new StringBuilder();
        private readonly object _streamLock = new object();
        private readonly System.Windows.Forms.Timer _streamFlushTimer;

        private AgentClient _agentClient;
        private CancellationTokenSource _turnCancellation;
        private Process _serviceProcess;

        public AgentTaskPaneControl()
        {
            Dock = DockStyle.Fill;
            BackColor = Color.FromArgb(242, 246, 248);

            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer, true);
            UpdateStyles();

            var root = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                ColumnCount = 1,
                RowCount = 4,
                Padding = new Padding(12),
            };
            root.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            root.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
            root.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            root.RowStyles.Add(new RowStyle(SizeType.AutoSize));

            var header = new TableLayoutPanel
            {
                Dock = DockStyle.Top,
                ColumnCount = 3,
                AutoSize = true,
            };
            header.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
            header.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 120));
            header.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 120));

            _serviceUrlBox = new TextBox
            {
                Dock = DockStyle.Fill,
                Text = "http://127.0.0.1:8000",
                Margin = new Padding(0, 0, 8, 8),
            };

            _restartServiceButton = new Button
            {
                Text = "Start Service",
                Dock = DockStyle.Fill,
                Margin = new Padding(0, 0, 8, 8),
                BackColor = Color.FromArgb(217, 243, 234),
            };
            _restartServiceButton.Click += async (sender, args) => await EnsureServiceRunningAsync();

            _sendButton = new Button
            {
                Text = "Send",
                Dock = DockStyle.Fill,
                Margin = new Padding(0, 0, 0, 8),
                BackColor = Color.FromArgb(19, 111, 99),
                ForeColor = Color.White,
            };
            _sendButton.Click += async (sender, args) => await SubmitAsync();

            header.Controls.Add(_serviceUrlBox, 0, 0);
            header.Controls.Add(_restartServiceButton, 1, 0);
            header.Controls.Add(_sendButton, 2, 0);

            _conversationBox = new RichTextBox
            {
                Dock = DockStyle.Fill,
                ReadOnly = true,
                BackColor = Color.White,
                BorderStyle = BorderStyle.FixedSingle,
                Font = new Font("Microsoft YaHei UI", 9.5f),
                HideSelection = true,
                DetectUrls = false,
                ScrollBars = RichTextBoxScrollBars.Vertical,
            };

            _inputBox = new TextBox
            {
                Dock = DockStyle.Fill,
                Multiline = true,
                Height = 90,
                Font = new Font("Microsoft YaHei UI", 10f),
            };

            _statusLabel = new Label
            {
                Dock = DockStyle.Top,
                AutoSize = true,
                Text = "Status: Ready",
                ForeColor = Color.FromArgb(15, 58, 91),
                Padding = new Padding(0, 8, 0, 0),
            };

            root.Controls.Add(header, 0, 0);
            root.Controls.Add(_conversationBox, 0, 1);
            root.Controls.Add(_inputBox, 0, 2);
            root.Controls.Add(_statusLabel, 0, 3);
            Controls.Add(root);

            _agentClient = new AgentClient(_serviceUrlBox.Text);
            _streamFlushTimer = new System.Windows.Forms.Timer { Interval = StreamFlushIntervalMs };
            _streamFlushTimer.Tick += FlushTimerTick;
        }

        internal async Task InitializeAsync()
        {
            await EnsureServiceRunningAsync();
            AppendSystemMessage("Plugin loaded. Enter a request and the add-in will forward it to the multi-agent workflow.");
        }

        private async Task SubmitAsync()
        {
            var message = _inputBox.Text.Trim();
            if (string.IsNullOrWhiteSpace(message))
            {
                return;
            }

            _agentClient.UpdateBaseUrl(_serviceUrlBox.Text);
            SetBusy(true, "Status: Calling local agent service...");
            AppendMessage("User", message, Color.FromArgb(232, 241, 255));
            _inputBox.Clear();

            _turnCancellation?.Cancel();
            _turnCancellation = new CancellationTokenSource();

            try
            {
                await _agentClient.StreamChatAsync(
                    message,
                    onMessageStart: async (role, agentName) =>
                    {
                        var displayName = string.IsNullOrWhiteSpace(agentName) ? "Agent" : agentName;
                        await InvokeAsync(() =>
                        {
                            FlushPendingStreamText();
                            BeginAgentMessage(displayName);
                        });
                    },
                    onDelta: async delta =>
                    {
                        await InvokeAsync(() => BufferAgentMessage(delta));
                    },
                    onAuxiliaryEvent: async (title, content) =>
                    {
                        await InvokeAsync(() =>
                        {
                            FlushPendingStreamText();
                            AppendMessage(title, content, Color.FromArgb(232, 250, 246));
                        });
                    },
                    cancellationToken: _turnCancellation.Token);

                FlushPendingStreamText();
                SetBusy(false, "Status: Turn complete");
            }
            catch (Exception ex)
            {
                FlushPendingStreamText();
                AppendMessage("Error", ex.Message, Color.MistyRose);
                SetBusy(false, "Status: Request failed");
            }
        }

        private async Task EnsureServiceRunningAsync()
        {
            try
            {
                if (_serviceProcess != null && !_serviceProcess.HasExited)
                {
                    SetBusy(false, "Status: Local agent service is already running");
                    return;
                }

                var repoRoot = ResolveRepoRoot();
                var startInfo = new ProcessStartInfo
                {
                    FileName = "cmd.exe",
                    Arguments = "/c uv run python -m multi_agent_src.web_demo",
                    WorkingDirectory = repoRoot,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                };

                _serviceProcess = Process.Start(startInfo);
                await Task.Delay(1500);
                SetBusy(false, "Status: Attempted to start the local agent service");
            }
            catch (Exception ex)
            {
                AppendMessage(
                    "System",
                    "Automatic service startup failed. Run `uv run python -m multi_agent_src.web_demo` in the repo root first.\n" + ex.Message,
                    Color.Moccasin);
                SetBusy(false, "Status: Service not started");
            }
        }

        private string ResolveRepoRoot()
        {
            var baseDir = AppDomain.CurrentDomain.BaseDirectory;
            return Path.GetFullPath(Path.Combine(baseDir, "..", "..", "..", ".."));
        }

        private void BeginAgentMessage(string agentName)
        {
            AppendMessage(agentName, string.Empty, Color.FromArgb(236, 250, 246));
        }

        private void BufferAgentMessage(string delta)
        {
            bool shouldFlushImmediately;
            lock (_streamLock)
            {
                _streamBuffer.Append(delta);
                shouldFlushImmediately = _streamBuffer.Length >= StreamFlushThresholdChars;
            }

            if (shouldFlushImmediately)
            {
                FlushPendingStreamText();
                return;
            }

            if (!_streamFlushTimer.Enabled)
            {
                _streamFlushTimer.Start();
            }
        }

        private void FlushTimerTick(object sender, EventArgs e)
        {
            FlushPendingStreamText();
        }

        private void FlushPendingStreamText()
        {
            string chunk;
            lock (_streamLock)
            {
                if (_streamBuffer.Length == 0)
                {
                    _streamFlushTimer.Stop();
                    return;
                }

                chunk = _streamBuffer.ToString();
                _streamBuffer.Clear();
            }

            AppendStreamChunk(chunk);
        }

        private void AppendStreamChunk(string chunk)
        {
            if (string.IsNullOrEmpty(chunk))
            {
                return;
            }

            SuspendConversationRedraw();
            try
            {
                _conversationBox.SelectionStart = _conversationBox.TextLength;
                _conversationBox.SelectionLength = 0;
                _conversationBox.SelectionColor = Color.FromArgb(22, 48, 66);
                _conversationBox.AppendText(chunk);
            }
            finally
            {
                ResumeConversationRedraw();
            }

            _conversationBox.ScrollToCaret();
        }

        private void AppendSystemMessage(string text)
        {
            AppendMessage("System", text, Color.FromArgb(232, 250, 246));
        }

        private void AppendMessage(string sender, string content, Color backColor)
        {
            SuspendConversationRedraw();
            try
            {
                _conversationBox.SelectionStart = _conversationBox.TextLength;
                _conversationBox.SelectionLength = 0;
                _conversationBox.SelectionBackColor = backColor;
                _conversationBox.SelectionColor = Color.FromArgb(15, 58, 91);
                _conversationBox.SelectionFont = new Font(_conversationBox.Font, FontStyle.Bold);
                _conversationBox.AppendText(sender + Environment.NewLine);
                _conversationBox.SelectionFont = new Font(_conversationBox.Font, FontStyle.Regular);
                _conversationBox.SelectionColor = Color.FromArgb(22, 48, 66);

                if (!string.IsNullOrEmpty(content))
                {
                    _conversationBox.AppendText(content);
                }

                _conversationBox.AppendText(Environment.NewLine + Environment.NewLine);
                _conversationBox.SelectionBackColor = _conversationBox.BackColor;
            }
            finally
            {
                ResumeConversationRedraw();
            }

            _conversationBox.ScrollToCaret();
        }

        private void SuspendConversationRedraw()
        {
            if (_conversationBox.IsHandleCreated)
            {
                SendMessage(_conversationBox.Handle, WmSetRedraw, IntPtr.Zero, IntPtr.Zero);
            }
        }

        private void ResumeConversationRedraw()
        {
            if (_conversationBox.IsHandleCreated)
            {
                SendMessage(_conversationBox.Handle, WmSetRedraw, new IntPtr(1), IntPtr.Zero);
                _conversationBox.Invalidate();
                _conversationBox.Update();
            }
        }

        private void SetBusy(bool isBusy, string status)
        {
            _sendButton.Enabled = !isBusy;
            _inputBox.Enabled = !isBusy;
            _serviceUrlBox.Enabled = !isBusy;
            _restartServiceButton.Enabled = !isBusy;
            _statusLabel.Text = status;
        }

        private Task InvokeAsync(Action action)
        {
            if (IsHandleCreated && InvokeRequired)
            {
                return Task.Factory.FromAsync(BeginInvoke(action), EndInvoke);
            }

            action();
            return Task.CompletedTask;
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                _streamFlushTimer?.Stop();
                _streamFlushTimer?.Dispose();
                _turnCancellation?.Cancel();
                _turnCancellation?.Dispose();
                _agentClient?.Dispose();
            }

            base.Dispose(disposing);
        }
    }
}
