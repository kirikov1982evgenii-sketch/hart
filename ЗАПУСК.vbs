Set sh = CreateObject("WScript.Shell")
folder = Replace(WScript.ScriptFullName, WScript.ScriptName, "")
sh.CurrentDirectory = folder
sh.Run "cmd /k cd /d """ & folder & """ && python run.py", 1, False
