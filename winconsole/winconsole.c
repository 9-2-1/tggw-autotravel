#include <stdalign.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <windows.h>

#define MSG_SIZE 32768
char *default_cmdline = "cmd.exe";

char *make_pipe_name()
{
    char *pipe_name = (char *)malloc(256);
    DWORD pid = GetCurrentProcessId();
    DWORD pipe_id = 0;
#if RAND_MAX < 0x100
#error "RAND_MAX is too small"
#endif
    for (int i = 0; i < 4; i++)
    {
        pipe_id = pipe_id * 0x100 + rand() % 0x100;
    }
    sprintf(pipe_name, "\\\\.\\pipe\\tggw_autotravel_winconsole_%08lx_%08lx", pid, pipe_id);
    return pipe_name;
}

void free_pipe_name(char *pipe_name)
{
    free(pipe_name);
}

#pragma pack(push, 1)

#define QUERY_SCREEN 1
#define QUERY_WRITE 2
#define QUERY_ALIVE 3
#define QUERY_KILL 4
#define QUERY_QUIT 0
// uint8_t mode;

struct QueryWrite
{
    uint16_t charCode;
#define M_CTRL 0x01
#define M_SHIFT 0x02
#define M_ALT 0x04
    uint8_t modifiers; // ctrl shift alt
};

#define REPLY_NONE 0
#define REPLY_LOG 1
#define REPLY_ERROR 2
#define REPLY_SCREEN 3
#define REPLY_ALIVE 4

struct ReplyScreen
{
    uint16_t lines;
    uint16_t columns; //
    struct ReplyScreenCursor
    {
        uint16_t x;
        uint16_t y;
        uint8_t visibility;
    } cursor;
    struct ReplyScreenChar
    {
        uint16_t charCode;
        uint8_t color;
    } buffer[1]; // lines * columns
};

struct ReplyText // Log/Error
{
    uint16_t length;
    char error[1];
};

#pragma pack(pop)

void printHex(const char *buf, size_t size)
{
    const char hexland[16] = "0123456789abcdef";
    char *chdata = (char *)malloc(size * 2 + 1);
    memset(chdata, '+', size * 2 + 1);
    for (int i = 0; i < size; i++)
    {
        unsigned char ch = buf[i];
        chdata[i * 2] = hexland[ch / 16];
        chdata[i * 2 + 1] = hexland[ch % 16];
    }
    chdata[size * 2] = '\0';
    puts(chdata);
    free(chdata);
}

#define R_SUCCESS 0
#define R_ERROR 1
#define R_STOP 2
int readPipe(HANDLE hPipe, char *replybuf, size_t *replysize)
{
    // Receive from process, and handle Error and Log
    DWORD dwBytesTransferred;
    OVERLAPPED ol;
    memset(&ol, 0, sizeof(ol));
    ol.hEvent = CreateEvent(NULL, TRUE, FALSE, NULL);
    BOOL ret = R_SUCCESS;
    while (TRUE)
    {
        BOOL result = ReadFile(hPipe, replybuf, MSG_SIZE, &dwBytesTransferred, &ol);
        // assume that the process will not terminate before pipe broken
        // so just get it synchonously
        if (!result)
        {
            DWORD lasterror = GetLastError();
            if (lasterror == ERROR_IO_PENDING)
            {
                result = GetOverlappedResult(hPipe, &ol, &dwBytesTransferred, TRUE);
            }
        }

        if (!result)
        {
            DWORD lasterror = GetLastError();
            if (lasterror == ERROR_NO_DATA)
            {
                printf("L ReadFile No data.\n");
            }
            else if (lasterror == ERROR_BAD_PIPE)
            {
                printf("X ReadFile Bad pipe.\n");
            }
            else if (lasterror == ERROR_BROKEN_PIPE)
            {
                printf("X ReadFile Broken pipe.\n");
            }
            else
            {
                printf("X ReadFile failed (%lu).\n", lasterror);
            }
            ret = R_STOP;
            break;
        }

        *replysize = dwBytesTransferred;
        if (*replysize >= 1)
        {
            uint8_t mode = replybuf[0];
            if (mode == REPLY_ERROR)
            {
                const struct ReplyText *replytext = (struct ReplyText *)&replybuf[1];
                printf("X %.*s\n", replytext->length, replytext->error);
                fflush(stdout);
                ret = R_ERROR;
                break;
            }
            else if (mode == REPLY_LOG)
            {
                const struct ReplyText *replytext = (struct ReplyText *)&replybuf[1];
                printf("L %.*s\n", replytext->length, replytext->error);
                fflush(stdout);
                // continue the loop to read real result
            }
            else
            {
                printHex(replybuf, *replysize);
                fflush(stdout);
                break;
            }
        }
    }

    CloseHandle(ol.hEvent);
    return ret;
}

int server(int arg_nostart, int arg_newconsole)
{
    DWORD dwBytesTransferred;
    char *pipename = make_pipe_name();
    DWORD openmode = PIPE_ACCESS_DUPLEX | FILE_FLAG_FIRST_PIPE_INSTANCE | FILE_FLAG_OVERLAPPED;
#ifndef PIPE_REJECT_REMOTE_CLIENTS
#define PIPE_REJECT_REMOTE_CLIENTS 0x00000008
#endif
    DWORD pipemode = PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE | PIPE_WAIT;
    if (!arg_nostart)
    {
        // Unshare the pipe with other processes.
        pipemode |= PIPE_REJECT_REMOTE_CLIENTS;
    }

    HANDLE hPipe = CreateNamedPipeA(pipename, openmode, pipemode, 1, 65536, 65536, 0, NULL);
    if (hPipe == INVALID_HANDLE_VALUE)
    {
        printf("X CreateNamedPipe failed (%lu).\n", GetLastError());
        free_pipe_name(pipename);
        return 1;
    }
    HANDLE hProcessWait = INVALID_HANDLE_VALUE;

    if (arg_nostart == 1)
    {
        printf("L %s\n", pipename);
        hProcessWait = CreateEventA(NULL, TRUE, FALSE, NULL); // Dummy event
    }
    else
    {
        char *progname = (char *)malloc(MSG_SIZE);
        GetModuleFileNameA(NULL, progname, MSG_SIZE);

        char *cmdline = (char *)malloc(MSG_SIZE);
        // copy args
        snprintf(cmdline, MSG_SIZE, "%s -p \"%s\"", GetCommandLineA(), pipename);

        STARTUPINFO si;
        PROCESS_INFORMATION pi;
        ZeroMemory(&si, sizeof(si));
        si.cb = sizeof(si);
        DWORD dwFlags = arg_newconsole == 1 ? CREATE_NEW_CONSOLE : CREATE_NO_WINDOW;
        if (!CreateProcessA(progname, cmdline, NULL, NULL, FALSE, dwFlags, NULL, NULL, &si, &pi))
        {
            printf("X CreateProcess failed (%lu).\n", GetLastError());
            free(cmdline);
            return 1;
        }

        free(progname);
        free(cmdline);

        hProcessWait = pi.hProcess;
    }

    free_pipe_name(pipename);

    HANDLE hPipeEvent = CreateEventA(NULL, TRUE, FALSE, NULL);
    HANDLE hWaits[2] = {hProcessWait, hPipeEvent};

    OVERLAPPED ol;
    ZeroMemory(&ol, sizeof(ol));
    ol.hEvent = hPipeEvent;

    int result = ConnectNamedPipe(hPipe, &ol);
    if (!result)
    {
        DWORD lasterror = GetLastError();
        if (lasterror == ERROR_IO_PENDING)
        {
            DWORD result2 = WaitForMultipleObjects(2, hWaits, FALSE, INFINITE);
            if (result2 == WAIT_OBJECT_0)
            {
                printf("L Process terminated.\n");
                CancelIo(hPipe);
                SetEvent(hPipeEvent);
                goto end;
            }
            else if (result2 == WAIT_OBJECT_0 + 1)
            {
                result = GetOverlappedResult(hPipe, &ol, &dwBytesTransferred, TRUE);
            }
            else
            {
                printf("X Internal Error.\n");
                goto end;
            }
        }
    }

    if (!result)
    {
        DWORD lasterror = GetLastError();
        if (lasterror == ERROR_PIPE_CONNECTED)
        {
            printf("L Pipe has been connected.\n");
            // no error
        }
        else
        {
            printf("X ConnectNamedPipe failed (%lu).\n", lasterror);
            goto end;
        }
    }
    else
    {
        printf("L Pipe has been connected.\n");
    }

    char *replybuf = (char *)malloc(MSG_SIZE);
    size_t replysize;
    char *inputbuf = (char *)malloc(MSG_SIZE);
    int stopped = 0;

    // Read Run Reply
    result = readPipe(hPipe, replybuf, &replysize);
    if (result == R_ERROR || result == R_STOP)
    {
        stopped = 1;
    }
    while (stopped == 0)
    {
        char *querybuf = NULL;
        size_t querysize = 0;
        DWORD inputlen = 0;
        scanf(" %32767[^\r\n]", inputbuf);
        inputlen = strlen(inputbuf);
        querybuf = malloc(inputlen / 2);
        querysize = 0;

        int firstdight = -1;
        for (int i = 0; i < inputlen; i++)
        {
            char ch = inputbuf[i];
            int v = -1;
            if (ch >= '0' && ch <= '9')
            {
                v = ch - '0';
            }
            else if (ch >= 'a' && ch <= 'f')
            {
                v = ch - 'a' + 10;
            }
            else if (ch >= 'A' && ch <= 'F')
            {
                v = ch - 'A' + 10;
            }
            else
            {
                continue;
            }
            if (firstdight == -1)
            {
                firstdight = v;
            }
            else
            {
                firstdight = firstdight * 16 + v;
                querybuf[querysize] = firstdight;
                querysize++;
                firstdight = -1;
            }
        }

        // Special treat exit
        if (querysize >= sizeof(uint8_t))
        {
            if (querybuf[0] == QUERY_QUIT)
            {
                stopped = 1;
            }
        }

        // Send to process
        result = WriteFile(hPipe, querybuf, querysize, &dwBytesTransferred, &ol);
        // assume that the process will not terminate before pipe broken
        // so just get it synchonously
        if (!result)
        {
            DWORD lasterror = GetLastError();
            if (lasterror == ERROR_IO_PENDING)
            {
                result = GetOverlappedResult(hPipe, &ol, &dwBytesTransferred, TRUE);
            }
        }
        free(querybuf);
        querybuf = NULL;

        if (!result)
        {
            DWORD lasterror = GetLastError();
            if (lasterror == ERROR_BAD_PIPE)
            {
                printf("X WriteFile Bad pipe.\n");
                break;
            }
            else if (lasterror == ERROR_BROKEN_PIPE)
            {
                printf("X WriteFile Broken pipe.\n");
                break;
            }
            printf("X WriteFile failed (%lu).\n", lasterror);
            break;
        }

        result = readPipe(hPipe, replybuf, &replysize);
        if (result == R_STOP)
        {
            break;
        }
    }

    free(inputbuf);
    free(replybuf);
end:
    CloseHandle(hPipeEvent);
    FlushFileBuffers(hPipe);
    CloseHandle(hPipe);

    DWORD exitcode = 0;
    if (arg_nostart == 0)
    {
        WaitForSingleObject(hProcessWait, INFINITE);
        GetExitCodeProcess(hProcessWait, &exitcode);
        printf("L Client exitcode: %lu\n", exitcode);
    }
    CloseHandle(hProcessWait);
    return exitcode;
}

// Client

BOOL replyText(HANDLE hPipe, uint8_t mode, const char *format, va_list args)
{
    DWORD dwBytesTransferred;
    char *replybuf = (char *)malloc(MSG_SIZE);
    size_t replysize;
    replybuf[0] = mode;
    struct ReplyText *replytext = (struct ReplyText *)&replybuf[1];
    size_t errlen = vsnprintf(replytext->error, MSG_SIZE - 1 - (sizeof(struct ReplyText) - 1), format, args);
    replytext->length = errlen;
    replysize = 1 + sizeof(struct ReplyText) + errlen - 1;
    BOOL result = WriteFile(hPipe, replybuf, replysize, &dwBytesTransferred, NULL) != 0;
    free(replybuf);
    return result;
}

BOOL replyLog(HANDLE hPipe, const char *format, ...)
{
    va_list args;
    va_start(args, format);
    va_end(args);
    return replyText(hPipe, REPLY_LOG, format, args);
}

BOOL replyError(HANDLE hPipe, const char *format, ...)
{
    va_list args;
    va_start(args, format);
    va_end(args);
    return replyText(hPipe, REPLY_ERROR, format, args);
}

BOOL conResize(HANDLE hStdout, int arg_columns, int arg_lines, HANDLE hPipe)
{
    CONSOLE_SCREEN_BUFFER_INFO csbi;
    GetConsoleScreenBufferInfo(hStdout, &csbi);
    SMALL_RECT win_rect = csbi.srWindow;
    COORD old_win_size = {win_rect.Right - win_rect.Left + 1, win_rect.Bottom - win_rect.Top + 1};
    COORD new_buf_size = {arg_columns, arg_lines};
    COORD large_buf_size = {max(old_win_size.X, new_buf_size.X), max(old_win_size.Y, new_buf_size.Y)};
    COORD max_win_size = GetLargestConsoleWindowSize(hStdout);
    COORD new_win_size = {min(max_win_size.X, new_buf_size.X), min(max_win_size.Y, new_buf_size.Y)};
    SMALL_RECT new_win_rect = {0, 0, new_win_size.X - 1, new_win_size.Y - 1};
    BOOL result;
    result = SetConsoleScreenBufferSize(hStdout, large_buf_size);
    if (!result)
    {
        replyLog(hPipe, "SetConsoleScreenBufferSize failed (%lu).", GetLastError());
        return FALSE;
    }
    result = SetConsoleWindowInfo(hStdout, TRUE, &new_win_rect);
    if (!result)
    {
        replyLog(hPipe, "SetConsoleWindowInfo failed (%lu).", GetLastError());
        return FALSE;
    }
    result = SetConsoleScreenBufferSize(hStdout, new_buf_size);
    if (!result)
    {
        replyLog(hPipe, "SetConsoleScreenBufferSize failed (%lu).", GetLastError());
        return FALSE;
    }
    return TRUE;
}

BOOL WINAPI nobreak(DWORD dwCtrlType)
{
    switch (dwCtrlType)
    {
    case CTRL_C_EVENT:
    case CTRL_BREAK_EVENT:
        return TRUE;
    default:
        return FALSE;
    }
}

int client(const char *arg_pipename, const char *arg_cmdline, int arg_columns, int arg_lines)
{
    int ret = 0;
    HANDLE hPipe = CreateFileA(arg_pipename, GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, 0, NULL);
    if (hPipe == INVALID_HANDLE_VALUE)
    {
        printf("X CreateFile failed (%lu).\n", GetLastError());
        return 1;
    }

    DWORD pipeState = PIPE_READMODE_MESSAGE | PIPE_WAIT;
    SetNamedPipeHandleState(hPipe, &pipeState, NULL, NULL);

    HANDLE hStdin = GetStdHandle(STD_INPUT_HANDLE);
    HANDLE hStdout = GetStdHandle(STD_OUTPUT_HANDLE);
    conResize(hStdout, arg_columns, arg_lines, hPipe);

    char *querybuf = (char *)malloc(MSG_SIZE);
    size_t querysize;
    char *replybuf = NULL;
    size_t replysize = 0;
    int stopsign = 0;
    DWORD dwBytesTransferred;

    char *cmdline = (char *)malloc(strlen(arg_cmdline) + 1);
    STARTUPINFO si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    DWORD dwFlags = 0;
    strcpy(cmdline, arg_cmdline);
    if (!CreateProcessA(NULL, cmdline, NULL, NULL, FALSE, dwFlags, NULL, NULL, &si, &pi))
    {
        replyError(hPipe, "CreateProcess failed (%lu).", GetLastError());
        free(cmdline);
        ret = 2;
        goto end;
    }
    free(cmdline);

    SetConsoleCtrlHandler(nobreak, TRUE);

    // Started successfully
    replysize = 1;
    replybuf = (char *)malloc(replysize);
    replybuf[0] = REPLY_NONE;
    if (WriteFile(hPipe, replybuf, replysize, &dwBytesTransferred, NULL) == 0)
    {
        // TODO rename format->reply
        replyError(hPipe, "WriteFile failed (%lu).", GetLastError());
        ret = 3;
        stopsign = 1;
    }
    free(replybuf);
    replybuf = NULL;

    while (stopsign == 0)
    {
        BOOL result = ReadFile(hPipe, querybuf, MSG_SIZE, &dwBytesTransferred, NULL);
        if (!result)
        {
            break;
        }
        querysize = dwBytesTransferred;
        if (querysize < 1)
        {
            replyError(hPipe, "query size too small");
            goto next;
        }
        switch (querybuf[0])
        {
        case QUERY_SCREEN: {
            if (querysize != 1)
            {
                replyError(hPipe, "Incorrect query size");
                goto next;
            }
            CONSOLE_SCREEN_BUFFER_INFO csbi;
            if (!GetConsoleScreenBufferInfo(hStdout, &csbi))
            {
                replyLog(hPipe, "GetConsoleScreenBufferInfo failed (%lu).", GetLastError());
                ZeroMemory(&csbi, sizeof(csbi));
            }
            COORD scr_begin = {0, 0};
            CONSOLE_CURSOR_INFO cci;
            if (!GetConsoleCursorInfo(hStdout, &cci))
            {
                replyLog(hPipe, "GetConsoleCursorInfo failed (%lu).", GetLastError());
                ZeroMemory(&cci, sizeof(cci));
            }
            COORD scr_size = {csbi.srWindow.Right - csbi.srWindow.Left + 1,
                              csbi.srWindow.Bottom - csbi.srWindow.Top + 1};
            replysize = 1 + sizeof(struct ReplyScreen) + sizeof(struct ReplyScreenChar) * (scr_size.X * scr_size.Y - 1);
            replybuf = malloc(replysize);
            replybuf[0] = REPLY_SCREEN;
            struct ReplyScreen *state = (struct ReplyScreen *)&replybuf[1];
            state->lines = scr_size.Y;
            state->columns = scr_size.X;
            state->cursor.x = csbi.dwCursorPosition.X - csbi.srWindow.Left;
            state->cursor.y = csbi.dwCursorPosition.Y - csbi.srWindow.Top;
            state->cursor.visibility = cci.bVisible ? 1 : 0;
            CHAR_INFO *charinfo = (CHAR_INFO *)malloc(sizeof(CHAR_INFO) * scr_size.X * scr_size.Y);
            if (!ReadConsoleOutputW(hStdout, charinfo, scr_size, scr_begin, &csbi.srWindow))
            {
                replyError(hPipe, "ReadConsoleOutputW failed (%lu).", GetLastError());
                goto next;
            }
            for (int y = 0; y < scr_size.Y; y++)
            {
                for (int x = 0; x < scr_size.X; x++)
                {
                    CHAR_INFO *ci = &charinfo[y * scr_size.X + x];
                    struct ReplyScreenChar *rc = &state->buffer[y * scr_size.X + x];
                    rc->charCode = ci->Char.UnicodeChar;
                    rc->color = ci->Attributes & 0xff;
                }
            }
        }
        break;
        case QUERY_WRITE: {
            if (querysize != 1 + sizeof(struct QueryWrite))
            {
                replyError(hPipe, "Incorrect query size");
                goto next;
            }
            const struct QueryWrite *qw = (struct QueryWrite *)&querybuf[1];
            // RIGHT_ALT_PRESSED 0x0001	按下右 ALT 键。
            // LEFT_ALT_PRESSED 0x0002	按下左 ALT 键。
            // RIGHT_CTRL_PRESSED 0x0004	按下右 CTRL 键。
            // LEFT_CTRL_PRESSED 0x0008	按下左 CTRL 键。
            // SHIFT_PRESSED 0x0010 按下 SHIFT 键。
            // NUMLOCK_ON 0x0020	NUM LOCK 指示灯亮起。
            // SCROLLLOCK_ON 0x0040	SCROLL LOCK 指示灯亮起。
            // CAPSLOCK_ON 0x0080	CAPS LOCK 指示灯亮起。
            // ENHANCED_KEY 0x0100	按键已增强。 请参阅注解。
            DWORD dwControlKeyState = 0;
            if (qw->modifiers & M_CTRL)
            {
                dwControlKeyState |= LEFT_CTRL_PRESSED;
            }
            if (qw->modifiers & M_SHIFT)
            {
                dwControlKeyState |= SHIFT_PRESSED;
            }
            if (qw->modifiers & M_ALT)
            {
                dwControlKeyState |= LEFT_ALT_PRESSED;
            }

            INPUT_RECORD inputs[2];
            DWORD eventWritten;
            ZeroMemory(inputs, sizeof(inputs) * 2);
            inputs[0].EventType = KEY_EVENT;
            inputs[0].Event.KeyEvent.bKeyDown = TRUE;
            inputs[0].Event.KeyEvent.wRepeatCount = 1;
            inputs[0].Event.KeyEvent.uChar.UnicodeChar = qw->charCode;
            inputs[0].Event.KeyEvent.wVirtualKeyCode = 0;
            inputs[0].Event.KeyEvent.wVirtualScanCode = 0;
            inputs[0].Event.KeyEvent.dwControlKeyState = dwControlKeyState;
            inputs[1].EventType = KEY_EVENT;
            inputs[1].Event.KeyEvent.bKeyDown = FALSE;
            inputs[1].Event.KeyEvent.wRepeatCount = 1;
            inputs[1].Event.KeyEvent.uChar.UnicodeChar = qw->charCode;
            inputs[1].Event.KeyEvent.wVirtualKeyCode = 0;
            inputs[1].Event.KeyEvent.wVirtualScanCode = 0;
            inputs[1].Event.KeyEvent.dwControlKeyState = dwControlKeyState;
            result = WriteConsoleInputW(hStdin, inputs, 2, &eventWritten);
            if (!result)
            {
                replyError(hPipe, "WriteConsoleInputW failed (%lu).", GetLastError());
                goto next;
            }
            replysize = sizeof(uint8_t);
            replybuf = (char *)malloc(replysize);
            replybuf[0] = REPLY_NONE;
        }
        break;
        case QUERY_ALIVE: {
            if (querysize != 1)
            {
                replyError(hPipe, "Incorrect query size");
                goto next;
            }
            replysize = 2;
            replybuf = (char *)malloc(replysize);
            replybuf[0] = REPLY_ALIVE;
            result = WaitForSingleObject(pi.hProcess, 0);
            if (result == WAIT_OBJECT_0)
            {
                replybuf[1] = 0;
            }
            else if (result == WAIT_TIMEOUT)
            {
                replybuf[1] = 1;
            }
            else
            {
                replyError(hPipe, "WaitForSingleObject failed (%lu).", GetLastError());
                goto next;
            }
        }
        break;
        case QUERY_KILL: {
            if (querysize != 1)
            {
                replyError(hPipe, "Incorrect query size");
                goto next;
            }
            if (!TerminateProcess(pi.hProcess, 0))
            {
                replyError(hPipe, "TerminateProcess failed (%lu).", GetLastError());
                goto next;
            }
            replysize = 1;
            replybuf = (char *)malloc(replysize);
            replybuf[0] = REPLY_NONE;
        }
        break;
        case QUERY_QUIT: {
            if (querysize != 1)
            {
                replyError(hPipe, "Incorrect query size");
                goto next;
            }
            stopsign = 1;
            replysize = 1;
            replybuf = (char *)malloc(replysize);
            replybuf[0] = REPLY_NONE;
        }
        break;
        default: {
            replyError(hPipe, "Wrong query mode %d", querybuf[0]);
            goto next;
        }
        }
        if (WriteFile(hPipe, replybuf, replysize, &dwBytesTransferred, NULL) == 0)
        {
            break;
        }
    next:
        if (replybuf != NULL)
        {
            free(replybuf);
            replybuf = NULL;
        }
    }
    if (WaitForSingleObject(pi.hProcess, 0) != WAIT_OBJECT_0)
    {
        TerminateProcess(pi.hProcess, 0x127);
    }
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    SetConsoleCtrlHandler(nobreak, FALSE);
    free(querybuf);
end:
    FlushFileBuffers(hPipe);
    CloseHandle(hPipe);
    return ret;
}

const char *HELP_STR = "\
Usage: winconsole [options]\n\
Options:\n\
  -h          Show this help\n\
  -c <cmd>    Command to run (default: cmd.exe)\n\
  -p <pipe>   Connect to existing pipe (server mode if omitted)\n\
  -L <lines>  Console lines (default: 24)\n\
  -C <cols>   Console columns (default: 80)\n\
  -n          Show new console for subprocess\n\
  -P          Print pipe name and wait (no auto-start)\
";

int main(int argc, char *argv[])
{
    srand(time(NULL));

    const char *arg_cmdline = default_cmdline;
    const char *arg_pipename = NULL;
    int arg_columns = 80;
    int arg_lines = 24;
    int arg_nostart = 0;
    int arg_newconsole = 0;
    for (int i = 1; i < argc; i++)
    {
        if (strcmp(argv[i], "-h") == 0)
        {
            puts(HELP_STR);
            return 0;
        }
        else if (strcmp(argv[i], "-c") == 0)
        {
            if (i + 1 >= argc)
            {
                printf("X Missing argument for -c option\n");
                return 1;
            }
            arg_cmdline = argv[++i];
        }
        else if (strcmp(argv[i], "-p") == 0)
        {
            if (i + 1 >= argc)
            {
                printf("X Missing argument for -p option\n");
                return 1;
            }
            arg_pipename = argv[++i];
        }
        else if (strcmp(argv[i], "-L") == 0)
        {
            if (i + 1 >= argc)
            {
                printf("Missing argument for -L option\n");
                return 1;
            }
            arg_lines = atoi(argv[++i]);
            if (arg_lines <= 0)
            {
                printf("Invalid value for -L option\n");
                return 1;
            }
        }
        else if (strcmp(argv[i], "-C") == 0)
        {
            if (i + 1 >= argc)
            {
                printf("Missing argument for -C option\n");
                return 1;
            }
            arg_columns = atoi(argv[++i]);
            if (arg_columns <= 0)
            {
                printf("Invalid value for -C option\n");
                return 1;
            }
        }
        else if (strcmp(argv[i], "-n") == 0)
        {
            arg_newconsole = 1;
        }
        else if (strcmp(argv[i], "-P") == 0)
        {
            arg_nostart = 1;
        }
        else
        {
            printf("Unknown option: %s\n", argv[i]);
            return 1;
        }
    }

    const char *pipename = arg_pipename;
    if (pipename == NULL)
    {
        return server(arg_nostart, arg_newconsole);
    }

    return client(pipename, arg_cmdline, arg_columns, arg_lines);
}
