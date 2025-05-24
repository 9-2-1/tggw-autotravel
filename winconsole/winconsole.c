#include <stdalign.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <windows.h>

#define eprintf(...) fprintf(stderr, __VA_ARGS__)
#define eputs(s) fputs(s, stderr)
#define pputs(s) fputs(s, stdout)

#define MSG_SIZE 32768
#define MAX_INPUT_EVENT 64
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

struct Query
{
#define QUERY_STATE 0
#define QUERY_INPUT 1
#define QUERY_RESIZE 2
#define QUERY_QUIT 3
    uint8_t mode;
    union QueryUnion {
        struct QueryInput
        {
            uint16_t count;
            INPUT_RECORD inputs[1]; // count
        } input;
        struct QueryResize
        {
            uint16_t lines;
            uint16_t columns;
        } resize;
    } data;
};

struct Reply
{
#define REPLY_NONE 0
#define REPLY_STATE 1
#define REPLY_ERROR 2
    uint8_t mode;
    union ReplyUnion {
        struct ReplyState
        {
            uint16_t lines;
            uint16_t columns; //
            uint16_t cursorX;
            uint16_t cursorY;
            uint16_t cursorSize; //
            uint32_t inMode;
            uint32_t outMode;
            uint16_t outAttr;
            uint8_t running;
            uint32_t exitCode;
            CHAR_INFO charinfo[1]; // lines * columns
        } state;
        char error[1];
    } data;
};

#pragma pack(pop)

void printHex(size_t size, char *buf)
{
    HANDLE hStdout = GetStdHandle(STD_OUTPUT_HANDLE);
    DWORD dwBytesTransferred;
    const char hexland[16] = "0123456789abcdef";
    char *chdata = (char *)malloc(size * 2 + 1);
    memset(chdata, '+', size * 2 + 1);
    for (int i = 0; i < size; i++)
    {
        unsigned char ch = buf[i];
        chdata[i * 2] = hexland[ch / 16];
        chdata[i * 2 + 1] = hexland[ch % 16];
    }
    chdata[size * 2] = '\n';
    if (!WriteFile(hStdout, chdata, size * 2 + 1, &dwBytesTransferred, NULL))
    {
        eprintf("WriteFile failed (%lu).\n", GetLastError());
    }
    // if (!FlushFileBuffers(hStdout))
    // {
    //     eprintf("FlushFileBuffers failed (%lu).\n", GetLastError());
    // }
    free(chdata);
}

int server(int arg_nostart, int arg_newconsole, int arg_inputmode)
{
    DWORD dwBytesTransferred;
    // server
    char *pipename = make_pipe_name();
    DWORD openmode = PIPE_ACCESS_DUPLEX | FILE_FLAG_FIRST_PIPE_INSTANCE | FILE_FLAG_OVERLAPPED;
#ifndef PIPE_REJECT_REMOTE_CLIENTS
#define PIPE_REJECT_REMOTE_CLIENTS 0x00000008
#endif
    DWORD pipemode = PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE | PIPE_WAIT; // | PIPE_REJECT_REMOTE_CLIENTS;

    HANDLE hPipe = CreateNamedPipeA(pipename, openmode, pipemode, 1, 65536, 65536, 0, NULL);
    if (hPipe == INVALID_HANDLE_VALUE)
    {
        eprintf("CreateNamedPipe failed (%lu).\n", GetLastError());
        free_pipe_name(pipename);
        return 1;
    }
    HANDLE hProcessWait = INVALID_HANDLE_VALUE;

    if (arg_nostart == 1)
    {
        printf("%s\n", pipename);
        hProcessWait = CreateEventA(NULL, TRUE, FALSE, NULL);
    }
    else
    {
        char *progname = (char *)malloc(MSG_SIZE);
        GetModuleFileNameA(NULL, progname, MSG_SIZE);

        char *cmdline = (char *)malloc(MSG_SIZE);
        snprintf(cmdline, MSG_SIZE, "%s -p \"%s\"", GetCommandLineA(), pipename);

        STARTUPINFO si;
        PROCESS_INFORMATION pi;
        ZeroMemory(&si, sizeof(si));
        si.cb = sizeof(si);
        DWORD dwFlags = arg_newconsole == 2 ? 0 : arg_newconsole == 1 ? CREATE_NEW_CONSOLE : CREATE_NO_WINDOW;
        if (!CreateProcessA(progname, cmdline, NULL, NULL, FALSE, dwFlags, NULL, NULL, &si, &pi))
        {
            eprintf("CreateProcess failed (%lu).\n", GetLastError());
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

    BOOL result = ConnectNamedPipe(hPipe, &ol);
    if (!result)
    {
        DWORD lasterror = GetLastError();
        if (lasterror == ERROR_IO_PENDING)
        {
            DWORD result2 = WaitForMultipleObjects(2, hWaits, FALSE, INFINITE);
            if (result2 == WAIT_OBJECT_0)
            {
                eprintf("Process terminated.\n");
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
                eprintf("Internal Error.\n");
                goto end;
            }
        }
    }

    if (!result)
    {
        DWORD lasterror = GetLastError();
        if (lasterror == ERROR_PIPE_CONNECTED)
        {
            eprintf("Pipe has been connected.\n");
            // no error
        }
        else
        {
            eprintf("ConnectNamedPipe failed (%lu).\n", lasterror);
            goto end;
        }
    }
    else
    {
        eprintf("Pipe has been connected.\n");
    }

    char *replybuf = (char *)malloc(MSG_SIZE);
    size_t replysize;

    HANDLE hStdin = GetStdHandle(STD_INPUT_HANDLE);
    HANDLE hStdout = GetStdHandle(STD_OUTPUT_HANDLE);

    DWORD dwOldMode = 0;
    GetConsoleMode(hStdin, &dwOldMode);

    char *inputbuf = (char *)malloc(MSG_SIZE);
    int stopped = 0;
    while (stopped == 0)
    {
        char *querybuf = NULL;
        size_t querysize = 0;
        if (arg_inputmode == 0)
        {
            DWORD inputlen = 0;
            if (!ReadFile(hStdin, inputbuf, MSG_SIZE, &inputlen, NULL))
            {
                eprintf("ReadConsoleA failed. (%lu)\n", GetLastError());
                break;
            }
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
        }
        else
        {
            DWORD dwEventCount = 0;
            if (!GetNumberOfConsoleInputEvents(hStdin, &dwEventCount))
            {
                eprintf("GetNumberOfConsoleInputEvents failed (%lu).\n", GetLastError());
            }
            if (dwEventCount == 0)
            {
                querysize = sizeof(uint8_t);
                querybuf = (char *)malloc(querysize);
                struct Query *query = (struct Query *)querybuf;
                query->mode = QUERY_STATE;
                Sleep(10);
            }
            else
            {
                DWORD dwRead;
                querysize = sizeof(uint8_t) + sizeof(struct QueryInput) + sizeof(INPUT_RECORD) * (dwEventCount - 1);
                querybuf = (char *)malloc(querysize);
                struct Query *query = (struct Query *)querybuf;
                query->mode = QUERY_INPUT;
                CONSOLE_SCREEN_BUFFER_INFO csbi;
                if (!GetConsoleScreenBufferInfo(hStdout, &csbi))
                {
                    eprintf("GetConsoleScreenBufferInfo failed (%lu).\n", GetLastError());
                    ZeroMemory(&csbi, sizeof(csbi));
                }
                if (!ReadConsoleInputW(hStdin, query->data.input.inputs, dwEventCount, &dwRead))
                {
                    eprintf("ReadConsoleInput failed (%lu).\n", GetLastError());
                }
                query->data.input.count = dwRead;
                querysize = sizeof(uint8_t) + sizeof(struct QueryInput) + sizeof(INPUT_RECORD) * (dwRead - 1);
                for (int i = 0; i < dwRead; i++)
                {
                    INPUT_RECORD *ir = &query->data.input.inputs[i];
                    if (ir->EventType == MOUSE_EVENT)
                    {
                        ir->Event.MouseEvent.dwMousePosition.X -= csbi.srWindow.Left;
                        ir->Event.MouseEvent.dwMousePosition.Y -= csbi.srWindow.Top;
                    }
                }
                printHex(querysize, querybuf);
            }
        }

        // Special treat exit
        if (querysize >= sizeof(uint8_t))
        {
            if (((struct Query *)querybuf)->mode == QUERY_QUIT)
            {
                stopped = 1;
            }
        }

        result = TransactNamedPipe(hPipe, querybuf, querysize, replybuf, MSG_SIZE, &dwBytesTransferred, &ol);
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
            if (lasterror == ERROR_NO_DATA)
            {
                eprintf("No data.\n");
                break;
            }
            else if (lasterror == ERROR_BAD_PIPE)
            {
                eprintf("Bad pipe.\n");
                break;
            }
            else if (lasterror == ERROR_BROKEN_PIPE)
            {
                eprintf("Broken pipe.\n");
                break;
            }
            eprintf("TransactNamedPipe failed (%lu).\n", lasterror);
            break;
        }

        replysize = dwBytesTransferred;
        if (arg_inputmode == 1)
        {
            struct Reply *reply = (struct Reply *)replybuf;
            if (replysize > sizeof(uint8_t))
            {
                if (reply->mode == REPLY_ERROR)
                {
                    eprintf("Error: %s\n", reply->data.error);
                }
                else if (reply->mode == REPLY_STATE)
                {
                    struct ReplyState *state = &reply->data.state;
                    if (replysize >= sizeof(uint8_t) + sizeof(struct ReplyState))
                    {
                        SetConsoleMode(hStdin, state->inMode);
                    }
                }
            }
        }
        else
        {
            printHex(replysize, replybuf);
        }
    }

end:
    SetConsoleMode(hStdin, dwOldMode);
    free(inputbuf);
    free(replybuf);
    CloseHandle(hPipeEvent);
    FlushFileBuffers(hPipe);
    CloseHandle(hPipe);

    DWORD exitcode = 0;
    if (arg_nostart == 0)
    {
        WaitForSingleObject(hProcessWait, INFINITE);
        GetExitCodeProcess(hProcessWait, &exitcode);
        eprintf("Client exitcode: %lu\n", exitcode);
    }
    CloseHandle(hProcessWait);
    return exitcode;
}

BOOL conResize(HANDLE hStdout, int arg_columns, int arg_lines)
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
        eprintf("SetConsoleScreenBufferSize failed (%lu).\n", GetLastError());
        return FALSE;
    }
    result = SetConsoleWindowInfo(hStdout, TRUE, &new_win_rect);
    if (!result)
    {
        eprintf("SetConsoleWindowInfo failed (%lu).\n", GetLastError());
        return FALSE;
    }
    result = SetConsoleScreenBufferSize(hStdout, new_buf_size);
    if (!result)
    {
        eprintf("SetConsoleScreenBufferSize failed (%lu).\n", GetLastError());
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

    HANDLE hPipe = CreateFileA(arg_pipename, GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, 0, NULL);
    if (hPipe == INVALID_HANDLE_VALUE)
    {
        eprintf("CreateFile failed (%lu).\n", GetLastError());
        return 1;
    }

    DWORD state = PIPE_READMODE_MESSAGE | PIPE_WAIT;
    SetNamedPipeHandleState(hPipe, &state, NULL, NULL);

    HANDLE hStdin = GetStdHandle(STD_INPUT_HANDLE);
    HANDLE hStdout = GetStdHandle(STD_OUTPUT_HANDLE);
    conResize(hStdout, arg_columns, arg_lines);

    char *cmdline = (char *)malloc(strlen(arg_cmdline) + 1);
    STARTUPINFO si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    DWORD dwFlags = 0;
    strcpy(cmdline, arg_cmdline);
    if (!CreateProcessA(NULL, cmdline, NULL, NULL, FALSE, dwFlags, NULL, NULL, &si, &pi))
    {
        eprintf("CreateProcess failed (%lu).\n", GetLastError());
        puts(cmdline);
        free(cmdline);
        return 2;
    }
    free(cmdline);

    SetConsoleCtrlHandler(nobreak, TRUE);

    struct Query *querybuf = (struct Query *)malloc(MSG_SIZE);
    size_t querysize;
    struct Reply *replybuf = NULL;
    size_t replysize = 0;
    const char *errorstr = NULL;
    int stopsign = 0;
    while (stopsign == 0)
    {
        DWORD dwBytesTransferred;
        BOOL result = ReadFile(hPipe, querybuf, MSG_SIZE, &dwBytesTransferred, NULL);
        if (!result)
        {
            eprintf("ReadFile failed (%lu).\n", GetLastError());
            break;
        }
        else
        {
            querysize = dwBytesTransferred;
            if (querysize < sizeof(uint8_t))
            {
                errorstr = "query size too small";
                goto error;
            }
            if (querybuf->mode == QUERY_INPUT)
            {
                if (querysize < sizeof(uint8_t) + sizeof(struct QueryInput))
                {
                    errorstr = "query size too small";
                    goto error;
                }
                INPUT_RECORD *inputs = querybuf->data.input.inputs;
                DWORD eventcnts = querybuf->data.input.count;
                if (querysize != sizeof(uint8_t) + sizeof(struct QueryInput) + sizeof(INPUT_RECORD) * (eventcnts - 1))
                {
                    errorstr = "Incorrect query size";
                    goto error;
                }
                CONSOLE_SCREEN_BUFFER_INFO csbi;
                if (!GetConsoleScreenBufferInfo(hStdout, &csbi))
                {
                    eprintf("GetConsoleScreenBufferInfo failed (%lu).\n", GetLastError());
                    ZeroMemory(&csbi, sizeof(csbi));
                }
                for (int i = 0; i < eventcnts; i++)
                {
                    INPUT_RECORD *ir = &inputs[i];
                    if (ir->EventType == MOUSE_EVENT)
                    {
                        ir->Event.MouseEvent.dwMousePosition.X += csbi.srWindow.Left;
                        ir->Event.MouseEvent.dwMousePosition.Y += csbi.srWindow.Top;
                    }
                }
                DWORD eventWritten;
                result = WriteConsoleInputW(hStdin, inputs, eventcnts, &eventWritten);
                if (!result)
                {
                    eprintf("WriteConsoleInputW failed (%lu).\n", GetLastError());
                }
                replysize = sizeof(uint8_t);
                replybuf = (struct Reply *)malloc(replysize);
                replybuf->mode = REPLY_NONE;
            }
            else if (querybuf->mode == QUERY_RESIZE)
            {
                if (querysize != sizeof(uint8_t) + sizeof(struct QueryResize))
                {
                    errorstr = "Incorrect query size";
                    goto error;
                }
                int columns = querybuf->data.resize.columns;
                int lines = querybuf->data.resize.lines;
                conResize(hStdout, columns, lines);
                replysize = sizeof(uint8_t);
                replybuf = (struct Reply *)malloc(replysize);
                replybuf->mode = REPLY_NONE;
            }
            else if (querybuf->mode == QUERY_QUIT)
            {
                stopsign = 1;
                replysize = sizeof(uint8_t);
                replybuf = (struct Reply *)malloc(replysize);
                replybuf->mode = REPLY_NONE;
            }
            else if (querybuf->mode == QUERY_STATE)
            {
                if (querysize != sizeof(uint8_t))
                {
                    errorstr = "Incorrect query size";
                    goto error;
                }
                CONSOLE_SCREEN_BUFFER_INFO csbi;
                if (!GetConsoleScreenBufferInfo(hStdout, &csbi))
                {
                    eprintf("GetConsoleScreenBufferInfo failed (%lu).\n", GetLastError());
                    ZeroMemory(&csbi, sizeof(csbi));
                }
                COORD scr_begin = {0, 0};
                DWORD dwInMode;
                if (!GetConsoleMode(hStdin, &dwInMode))
                {
                    eprintf("GetConsoleMode failed (%lu).\n", GetLastError());
                    dwInMode = 0;
                }
                DWORD dwOutMode;
                if (!GetConsoleMode(hStdout, &dwOutMode))
                {
                    eprintf("GetConsoleMode failed (%lu).\n", GetLastError());
                    dwOutMode = 0;
                }
                CONSOLE_CURSOR_INFO cci;
                if (!GetConsoleCursorInfo(hStdout, &cci))
                {
                    eprintf("GetConsoleCursorInfo failed (%lu).\n", GetLastError());
                    ZeroMemory(&cci, sizeof(cci));
                }
                COORD scr_size = {csbi.srWindow.Right - csbi.srWindow.Left + 1,
                                  csbi.srWindow.Bottom - csbi.srWindow.Top + 1};
                replysize = sizeof(struct Reply) + (scr_size.X * scr_size.Y - 1) * sizeof(CHAR_INFO);
                replybuf = (struct Reply *)malloc(replysize);
                replybuf->mode = REPLY_STATE;
                struct ReplyState *state = &replybuf->data.state;
                state->lines = scr_size.Y;
                state->columns = scr_size.X;
                state->cursorX = csbi.dwCursorPosition.X - csbi.srWindow.Left;
                state->cursorY = csbi.dwCursorPosition.Y - csbi.srWindow.Top;
                state->inMode = dwInMode;
                state->outMode = dwOutMode;
                state->outAttr = csbi.wAttributes;
                state->cursorSize = cci.bVisible ? 0 : cci.dwSize;
                state->running = 0;
                state->exitCode = -1;
                if (WaitForSingleObject(pi.hProcess, 0) != WAIT_OBJECT_0)
                {
                    state->running = 1;
                }
                else
                {
                    DWORD dwExitCode;
                    if (GetExitCodeProcess(pi.hProcess, &dwExitCode) == 0)
                    {
                        eprintf("GetExitCodeProcess failed (%lu).\n", GetLastError());
                    }
                    state->exitCode = dwExitCode;
                }
                SMALL_RECT full_rect = {0, 0, csbi.dwSize.X - 1, csbi.dwSize.Y - 1};
                if (!ReadConsoleOutputW(hStdout, state->charinfo, scr_size, scr_begin, &csbi.srWindow))
                {
                    eprintf("ReadConsoleOutputW failed (%lu).\n", GetLastError());
                }
            }
            else
            {
                errorstr = "Unknown query mode";
            }
        error:
            if (errorstr != NULL)
            {
                if (replybuf != NULL)
                {
                    free(replybuf);
                }

                replysize = sizeof(uint8_t) + strlen(errorstr) + 1;
                replybuf = (struct Reply *)malloc(replysize);
                replybuf->mode = REPLY_ERROR;
                strcpy((char *)replybuf->data.error, errorstr);
                errorstr = NULL;
            }
            if (WriteFile(hPipe, replybuf, replysize, &dwBytesTransferred, NULL) == 0)
            {
                eprintf("WriteFile failed (%lu).\n", GetLastError());
                break;
            }
            free(replybuf);
            replybuf = NULL;
        }
    }
    if (WaitForSingleObject(pi.hProcess, 0) != WAIT_OBJECT_0)
    {
        TerminateProcess(pi.hProcess, 0x127);
    }
    SetConsoleCtrlHandler(nobreak, FALSE);
    free(querybuf);
    FlushFileBuffers(hPipe);
    CloseHandle(hPipe);
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    return 0;
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
  -N          Print pipe name and wait (no auto-start)\n\
  -i          Direct input and show input data (for debugging only, with -n)\n\
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
    int arg_inputmode = 0;

    eprintf("cmdline: %s\n", GetCommandLineA());
    for (int i = 1; i < argc; i++)
    {
        if (strcmp(argv[i], "-h") == 0)
        {
            pputs(HELP_STR);
            return 0;
        }
        else if (strcmp(argv[i], "-c") == 0)
        {
            if (i + 1 >= argc)
            {
                eputs("Missing argument for -c option\n");
                return 1;
            }
            arg_cmdline = argv[++i];
        }
        else if (strcmp(argv[i], "-p") == 0)
        {
            if (i + 1 >= argc)
            {
                eputs("Missing argument for -p option\n");
                return 1;
            }
            arg_pipename = argv[++i];
        }
        else if (strcmp(argv[i], "-L") == 0)
        {
            if (i + 1 >= argc)
            {
                eputs("Missing argument for -L option\n");
                return 1;
            }
            arg_lines = atoi(argv[++i]);
            if (arg_lines <= 0)
            {
                eputs("Invalid value for -L option\n");
                return 1;
            }
        }
        else if (strcmp(argv[i], "-C") == 0)
        {
            if (i + 1 >= argc)
            {
                eputs("Missing argument for -C option\n");
                return 1;
            }
            arg_columns = atoi(argv[++i]);
            if (arg_columns <= 0)
            {
                eputs("Invalid value for -C option\n");
                return 1;
            }
        }
        else if (strcmp(argv[i], "-n") == 0)
        {
            arg_newconsole = 1;
        }
        else if (strcmp(argv[i], "-s") == 0)
        {
            arg_newconsole = 2;
        }
        else if (strcmp(argv[i], "-N") == 0)
        {
            arg_nostart = 1;
        }
        else if (strcmp(argv[i], "-i") == 0)
        {
            arg_inputmode = 1;
        }
        else
        {
            eprintf("Unknown option: %s\n", argv[i]);
            return 1;
        }
    }

    const char *pipename = arg_pipename;
    if (pipename == NULL)
    {
        return server(arg_nostart, arg_newconsole, arg_inputmode);
    }

    return client(pipename, arg_cmdline, arg_columns, arg_lines);
}
