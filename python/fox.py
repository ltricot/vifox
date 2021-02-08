import socket
import vim


def sendcode():
    # get selection (code block)
    row, col = vim.current.window.cursor
    print(row, col)
    buf = vim.current.buffer

    lline = row - 1
    while lline > -1 and buf[lline]:
        lline -= 1

    rline = row
    while rline < len(buf) and buf[rline]:
        rline += 1

    code = '\n'.join(buf[lline + 1:rline])

    # send selected code
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect('/tmp/foxdot.sock')
    except socket.error:
        print('Could not connect to Foxdot client')
        return

    sock.sendall((code + '\n\n').encode())
