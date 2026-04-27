using Microsoft.Win32;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;
using SolidWorks.Interop.swpublished;
using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.Runtime.InteropServices;

namespace agent_addin
{
    [ComVisible(true)]
    [Guid(AddinConstants.AddinGuid)]
    [ClassInterface(ClassInterfaceType.AutoDispatch)]
    public class AgentAddin : ISwAddin
    {
        private readonly int[] _taskPaneIconSizes = { 20, 32, 40, 64, 96, 128 };

        private ISldWorks _swApp;
        private ICommandManager _commandManager;
        private int _addinCookie;
        private TaskpaneView _taskPaneView;
        private AgentTaskPaneControl _taskPaneControl;

        public bool ConnectToSW(object ThisSW, int Cookie)
        {
            _swApp = ThisSW as ISldWorks;
            if (_swApp == null)
            {
                throw new InvalidCastException(
                    "SolidWorks passed an unexpected COM object to ConnectToSW. The object could not be cast to ISldWorks.");
            }

            _addinCookie = Cookie;
            _swApp.SetAddinCallbackInfo2(0, this, Cookie);

            _commandManager = _swApp.GetCommandManager(Cookie);
            AddCommandManager();
            return true;
        }

        public bool DisconnectFromSW()
        {
            RemoveCommandManager();

            if (_taskPaneView != null)
            {
                _taskPaneView.DeleteView();
                _taskPaneView = null;
            }

            _taskPaneControl?.Dispose();
            _taskPaneControl = null;
            _commandManager = null;
            _swApp = null;
            return true;
        }

        public int ShowAgentPane()
        {
            if (_taskPaneControl == null)
            {
                CreateTaskPane();
            }

            return 0;
        }

        public int EnableShowAgentPane()
        {
            return 1;
        }

        private void AddCommandManager()
        {
            int errors = 0;
            var commandGroup = _commandManager.CreateCommandGroup2(
                AddinConstants.MainCommandGroupId,
                AddinConstants.Title,
                AddinConstants.Description,
                string.Empty,
                -1,
                true,
                ref errors);

            commandGroup.AddCommandItem2(
                "Open AI Agent Pane",
                -1,
                "Show the AI agent task pane.",
                "AI Agent",
                AddinConstants.MainCommandId,
                nameof(ShowAgentPane),
                nameof(EnableShowAgentPane),
                AddinConstants.MainCommandId,
                (int)swCommandItemType_e.swToolbarItem | (int)swCommandItemType_e.swMenuItem);

            commandGroup.HasToolbar = true;
            commandGroup.HasMenu = true;
            commandGroup.Activate();
        }

        private void RemoveCommandManager()
        {
            if (_commandManager != null)
            {
                _commandManager.RemoveCommandGroup(AddinConstants.MainCommandGroupId);
            }
        }

        private void CreateTaskPane()
        {
            if (_taskPaneView != null)
            {
                return;
            }

            object imageList = EnsureTaskPaneIcons();
            _taskPaneView = _swApp.CreateTaskpaneView3(imageList, AddinConstants.TaskPaneTitle);
            if (_taskPaneView == null)
            {
                string iconDir = Path.GetDirectoryName(GetType().Assembly.Location) ?? AppDomain.CurrentDomain.BaseDirectory;
                _swApp.SendMsgToUser2(
                    "Failed to create the AI Agent task pane. Check the generated icon files under: " + iconDir,
                    (int)swMessageBoxIcon_e.swMbStop,
                    (int)swMessageBoxBtn_e.swMbOk);
                return;
            }

            _taskPaneControl = (AgentTaskPaneControl)_taskPaneView.AddControl(AddinConstants.ProgId, string.Empty);
            if (_taskPaneControl == null)
            {
                _swApp.SendMsgToUser2(
                    "Failed to load the AI Agent task pane control. Confirm the COM registration and ProgId settings.",
                    (int)swMessageBoxIcon_e.swMbStop,
                    (int)swMessageBoxBtn_e.swMbOk);
                return;
            }

            _ = _taskPaneControl.InitializeAsync();
        }

        private string[] EnsureTaskPaneIcons()
        {
            string assemblyDir = Path.GetDirectoryName(GetType().Assembly.Location) ?? AppDomain.CurrentDomain.BaseDirectory;
            string[] iconPaths = new string[_taskPaneIconSizes.Length];

            for (int index = 0; index < _taskPaneIconSizes.Length; index++)
            {
                int size = _taskPaneIconSizes[index];
                string iconPath = Path.Combine(assemblyDir, $"agent_taskpane_icon_{size}.bmp");
                iconPaths[index] = iconPath;

                if (File.Exists(iconPath))
                {
                    continue;
                }

                using (var bitmap = new Bitmap(size, size))
                using (var graphics = Graphics.FromImage(bitmap))
                using (var accentBrush = new SolidBrush(Color.FromArgb(19, 111, 99)))
                using (var backgroundBrush = new SolidBrush(Color.FromArgb(242, 246, 248)))
                using (var textBrush = new SolidBrush(Color.White))
                using (var font = new Font("Segoe UI", Math.Max(8f, size / 3.2f), FontStyle.Bold, GraphicsUnit.Pixel))
                using (var format = new StringFormat { Alignment = StringAlignment.Center, LineAlignment = StringAlignment.Center })
                {
                    graphics.Clear(backgroundBrush.Color);
                    graphics.SmoothingMode = SmoothingMode.AntiAlias;

                    float margin = Math.Max(2f, size * 0.08f);
                    float circleSize = size - (margin * 2f);
                    graphics.FillEllipse(accentBrush, margin, margin, circleSize, circleSize);
                    graphics.DrawString("AI", font, textBrush, new RectangleF(0, 0, size, size), format);

                    bitmap.Save(iconPath);
                }
            }

            return iconPaths;
        }

        [ComRegisterFunction]
        public static void RegisterFunction(Type t)
        {
            RegisterAddin(t, true);
        }

        [ComUnregisterFunction]
        public static void UnregisterFunction(Type t)
        {
            RegisterAddin(t, false);
        }

        private static void RegisterAddin(Type type, bool register)
        {
            string addinKey = $@"SOFTWARE\SolidWorks\Addins\{{{type.GUID}}}";
            string startupKey = $@"Software\SolidWorks\AddInsStartup\{{{type.GUID}}}";

            if (register)
            {
                using (RegistryKey rk = Registry.LocalMachine.CreateSubKey(addinKey))
                {
                    rk.SetValue(null, 1, RegistryValueKind.DWord);
                    rk.SetValue("Title", AddinConstants.Title, RegistryValueKind.String);
                    rk.SetValue("Description", AddinConstants.Description, RegistryValueKind.String);
                }

                using (RegistryKey rk = Registry.CurrentUser.CreateSubKey(startupKey))
                {
                    rk.SetValue(null, 1, RegistryValueKind.DWord);
                }
            }
            else
            {
                Registry.LocalMachine.DeleteSubKeyTree(addinKey, false);
                Registry.CurrentUser.DeleteSubKeyTree(startupKey, false);
            }
        }
    }
}
