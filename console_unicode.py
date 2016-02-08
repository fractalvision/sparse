# -*- coding: utf-8 -*-
import sys
import codecs

def setup_console(sys_enc="utf-8"):
    reload(sys)
    try:
        # win32
        if sys.platform.startswith("win"):
            import ctypes
            enc = "cp%d" % ctypes.windll.kernel32.GetOEMCP() #TODO: win64/python64
        else:
            # Linux
            enc = (sys.stdout.encoding if sys.stdout.isatty() else
                        sys.stderr.encoding if sys.stderr.isatty() else
                            sys.getfilesystemencoding() or sys_enc)
        # sys
        sys.setdefaultencoding(sys_enc)

        if sys.stdout.isatty() and sys.stdout.encoding != enc:
            sys.stdout = codecs.getwriter(enc)(sys.stdout, 'replace')

        if sys.stderr.isatty() and sys.stderr.encoding != enc:
            sys.stderr = codecs.getwriter(enc)(sys.stderr, 'replace')

    except:
        pass