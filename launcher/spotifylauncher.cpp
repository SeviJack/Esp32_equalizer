#include <windows.h>
#include <tlhelp32.h>
#include <shellapi.h>

DWORD findProcessId(const char* name) {
    PROCESSENTRY32 entry = { sizeof(entry) };
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snapshot == INVALID_HANDLE_VALUE) return 0;

    DWORD pid = 0;
    if (Process32First(snapshot, &entry)) {
        do {
            if (!_stricmp(entry.szExeFile, name)) {
                pid = entry.th32ProcessID;
                break;
            }
        } while (Process32Next(snapshot, &entry));
    }
    CloseHandle(snapshot);
    return pid;
}

int WINAPI WinMain(HINSTANCE, HINSTANCE, LPSTR, int) {

    // Launch Spotify via CreateProcessW
    STARTUPINFOW si;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);

    PROCESS_INFORMATION pi;
    ZeroMemory(&pi, sizeof(pi));

    BOOL ok = CreateProcessW(
        L"C:\\Users\\fbook\\AppData\\Roaming\\Spotify\\Spotify.exe",
        NULL,
        NULL, NULL, FALSE,
        0, NULL, NULL,
        &si, &pi
    );

    // Launch equalizer if not already running
    if (findProcessId("desktopeq.exe") == 0) {
        ShellExecuteW(NULL, L"open", L"C:\\Tools\\desktopeq\\desktopeq.exe", NULL, NULL, SW_SHOW);
    }

    // Wait for Spotify to exit
    if (ok) {
        WaitForSingleObject(pi.hProcess, INFINITE);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    }

    // Kill equalizer
    DWORD eqPid = findProcessId("desktopeq.exe");
    if (eqPid) {
        HANDLE eqProc = OpenProcess(PROCESS_TERMINATE, FALSE, eqPid);
        TerminateProcess(eqProc, 0);
        CloseHandle(eqProc);
    }

    return 0;
}
