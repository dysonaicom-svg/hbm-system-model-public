/* config.h.  Generated from config.h.in by configure.  */
/* config.h.in.  Generated from configure.ac by autoheader.  */

/* Location of data files */
#define DATADIR "/home/ic/JXTF/HBM/tools/nvc/share/nvc"

/* Path to diff program */
#define DIFF_PATH "/usr/bin/diff"

/* Directory separator */
#define DIR_SEP "/"

/* Dynamic library extension */
#define DLL_EXT "so"

/* Enable default library search paths */
#define ENABLE_DEFAULT_PATHS 1

/* LLVM code generator enabled */
#define ENABLE_LLVM 1

/* TCL shell enabled */
/* #undef ENABLE_TCL */

/* Executable file extension */
#define EXEEXT ""

/* Enable FST glitch removal */
#define FST_REMOVE_DUPLICATE_VC 1

/* Target supports ARMv8 crypto instructions */
/* #undef HAVE_ARM_CRYPTO */

/* Define to 1 if you have the <arm_neon.h> header file. */
/* #undef HAVE_ARM_NEON_H */

/* Target supports AVX2 instructions */
#define HAVE_AVX2 1

/* Have capstone for diassembly */
/* #undef HAVE_CAPSTONE */

/* Define to 1 if a SysV or X/Open compatible Curses library is present */
/* #undef HAVE_CURSES */

/* Define to 1 if library supports color (enhanced functions) */
/* #undef HAVE_CURSES_COLOR */

/* Define to 1 if library supports X/Open Enhanced functions */
/* #undef HAVE_CURSES_ENHANCED */

/* Define to 1 if <curses.h> is present */
/* #undef HAVE_CURSES_H */

/* Define to 1 if library supports certain obsolete features */
/* #undef HAVE_CURSES_OBSOLETE */

/* Define to 1 if you have the 'fpurge' function. */
/* #undef HAVE_FPURGE */

/* Define to 1 if you have the 'fseeko' function. */
#define HAVE_FSEEKO 1

/* Define to 1 if you have the 'ftello' function. */
#define HAVE_FTELLO 1

/* Define to 1 if the system has the `returns_nonnull' function attribute */
#define HAVE_FUNC_ATTRIBUTE_RETURNS_NONNULL 1

/* Defined if getcontext is available */
#define HAVE_GETCONTEXT 1

/* Define to 1 if you have the 'getline' function. */
#define HAVE_GETLINE 1

/* Define to 1 if you have the 'gettid' function. */
#define HAVE_GETTID 1

/* Have Git commit hash */
#define HAVE_GIT_SHA 1

/* Define to 1 if you have the <history.h> header file. */
/* #undef HAVE_HISTORY_H */

/* Define to 1 if you have the <inttypes.h> header file. */
#define HAVE_INTTYPES_H 1

/* Have libdw for stack traces */
/* #undef HAVE_LIBDW */

/* Have libdwarf for stack traces */
/* #undef HAVE_LIBDWARF */

/* Define if you have a readline compatible library */
/* #undef HAVE_LIBREADLINE */

/* Defined if LLVM is available */
#define HAVE_LLVM 1

/* Define to 1 if you have the 'memmem' function. */
#define HAVE_MEMMEM 1

/* Define to 1 if you have the <minix/config.h> header file. */
/* #undef HAVE_MINIX_CONFIG_H */

/* Define to 1 if the Ncurses library is present */
/* #undef HAVE_NCURSES */

/* Define to 1 if the NcursesW library is present */
/* #undef HAVE_NCURSESW */

/* Define to 1 if <ncursesw/curses.h> is present */
/* #undef HAVE_NCURSESW_CURSES_H */

/* Define to 1 if <ncursesw.h> is present */
/* #undef HAVE_NCURSESW_H */

/* Define to 1 if <ncurses/curses.h> is present */
/* #undef HAVE_NCURSES_CURSES_H */

/* Define to 1 if <ncurses.h> is present */
/* #undef HAVE_NCURSES_H */

/* Defined if linker supports -no_fixup_chains */
/* #undef HAVE_NO_FIXUP_CHAINS */

/* Target supports POPCNT instructions */
#define HAVE_POPCNT 1

/* Define to 1 if you have the 'popen' function. */
#define HAVE_POPEN 1

/* Define if you have POSIX threads libraries and header files. */
#define HAVE_PTHREAD 1

/* Have PTHREAD_PRIO_INHERIT. */
#define HAVE_PTHREAD_PRIO_INHERIT 1

/* Define to 1 if you have the <readline.h> header file. */
/* #undef HAVE_READLINE_H */

/* Define if your readline library has \`add_history' */
/* #undef HAVE_READLINE_HISTORY */

/* Define to 1 if you have the <readline/history.h> header file. */
/* #undef HAVE_READLINE_HISTORY_H */

/* Define to 1 if you have the <readline/readline.h> header file. */
/* #undef HAVE_READLINE_READLINE_H */

/* Target supports SSE4.1 instructions */
#define HAVE_SSE41 1

/* Target supports SHA instructions */
#define HAVE_SSE_SHA 1

/* Define to 1 if you have the <stdint.h> header file. */
#define HAVE_STDINT_H 1

/* Define to 1 if you have the <stdio_ext.h> header file. */
#define HAVE_STDIO_EXT_H 1

/* Define to 1 if you have the <stdio.h> header file. */
#define HAVE_STDIO_H 1

/* Define to 1 if you have the <stdlib.h> header file. */
#define HAVE_STDLIB_H 1

/* Define to 1 if you have the 'strcasestr' function. */
#define HAVE_STRCASESTR 1

/* Define to 1 if you have the 'strchrnul' function. */
#define HAVE_STRCHRNUL 1

/* Define to 1 if you have the <strings.h> header file. */
#define HAVE_STRINGS_H 1

/* Define to 1 if you have the <string.h> header file. */
#define HAVE_STRING_H 1

/* Define to 1 if you have the 'strndup' function. */
#define HAVE_STRNDUP 1

/* Define to 1 if 'st_mtimespec.tv_nsec' is a member of 'struct stat'. */
/* #undef HAVE_STRUCT_STAT_ST_MTIMESPEC_TV_NSEC */

/* Define to 1 if 'st_mtim.tv_nsec' is a member of 'struct stat'. */
#define HAVE_STRUCT_STAT_ST_MTIM_TV_NSEC 1

/* Define to 1 if you have the <sys/prctl.h> header file. */
#define HAVE_SYS_PRCTL_H 1

/* Define to 1 if you have the <sys/ptrace.h> header file. */
#define HAVE_SYS_PTRACE_H 1

/* Define to 1 if you have the <sys/stat.h> header file. */
#define HAVE_SYS_STAT_H 1

/* Define to 1 if you have the <sys/types.h> header file. */
#define HAVE_SYS_TYPES_H 1

/* Define to 1 if you have the <sys/ucontext.h> header file. */
#define HAVE_SYS_UCONTEXT_H 1

/* Define to 1 if you have the 'tcgetwinsize' function. */
/* #undef HAVE_TCGETWINSIZE */

/* Define to 1 if you have the <ucontext.h> header file. */
#define HAVE_UCONTEXT_H 1

/* Define to 1 if you have the <unistd.h> header file. */
#define HAVE_UNISTD_H 1

/* Define to 1 if you have the <wchar.h> header file. */
#define HAVE_WCHAR_H 1

/* Define to 1 if the system has the `__builtin_setjmp' built-in function */
#define HAVE___BUILTIN_SETJMP 1

/* Define to 1 if you have the '__fpurge' function. */
#define HAVE___FPURGE 1

/* Import library required */
/* #undef IMPLIB_REQUIRED */

/* Installation library directory */
#define LIBDIR "/home/ic/JXTF/HBM/tools/nvc/lib/nvc"

/* Location of internal programs */
#define LIBEXECDIR "/home/ic/JXTF/HBM/tools/nvc/libexec/nvc"

/* Location of LLVM binaries */
#define LLVM_CONFIG_BINDIR "/usr/lib/llvm-18/bin"

/* LLVMDIBuilderCreateCompileUnit has SysRoot parameter */
#define LLVM_CREATE_CU_HAS_SYSROOT 1

/* LLVM has captures attribute */
/* #undef LLVM_HAS_CAPTURES */

/* LLVM has LLJIT API */
#define LLVM_HAS_LLJIT 1

/* LLVM uses opaque pointers by default */
#define LLVM_HAS_OPAQUE_POINTERS 1

/* LLVM has new pass manager */
#define LLVM_HAS_PASS_BUILDER 1

/* Have LLVMDIScopeGetFile */
#define LLVM_HAVE_DI_SCOPE_GET_FILE 1

/* Have LLVMSetCurrentDebugLocation2 */
#define LLVM_HAVE_SET_CURRENT_DEBUG_LOCATION_2 1

/* LLVM object file extension */
#define LLVM_OBJ_EXT "o"

/* LLVM uwtable attribute takes an argument */
#define LLVM_UWTABLE_HAS_ARGUMENT 1

/* Version of LLVM installed */
#define LLVM_VERSION "18.1.8"

/* Disable extra debugging checks for development */
#define NDEBUG 1

/* Name of package */
#define PACKAGE "nvc"

/* Define to the address where bug reports for this package should be sent. */
#define PACKAGE_BUGREPORT "https://github.com/nickg/nvc/issues"

/* Define to the full name of this package. */
#define PACKAGE_NAME "nvc"

/* Define to the full name and version of this package. */
#define PACKAGE_STRING "nvc 1.22-devel"

/* Define to the one symbol short name of this package. */
#define PACKAGE_TARNAME "nvc"

/* Define to the home page for this package. */
#define PACKAGE_URL "https://www.nickg.me.uk/nvc/"

/* Define to the version of this package. */
#define PACKAGE_VERSION "1.22-devel"

/* Path separator */
#define PATH_SEP ":"

/* Installation prefix */
#define PREFIX "/home/ic/JXTF/HBM/tools/nvc"

/* Preserve frame pointer for profiling */
/* #undef PRESERVE_FRAME_POINTER */

/* Define to necessary symbol if this constant uses a non-standard name on
   your system. */
/* #undef PTHREAD_CREATE_JOINABLE */

/* Path to POSIX shell */
#define SH_PATH "/usr/bin/sh"

/* Define to 1 if all of the C89 standard headers exist (not just the ones
   required in a freestanding environment). This macro is provided for
   backward compatibility; new code need not use it. */
#define STDC_HEADERS 1

/* Target system description for crash reports */
#define TARGET_SYSTEM "x86_64-pc-linux-gnu"

/* Location of testcases */
#define TESTDIR "/home/ic/JXTF/HBM/nvc_build/test"

/* Define to 1 if the target uses emutls for thread-local storage. */
/* #undef USE_EMUTLS */

/* Enable extensions on AIX, Interix, z/OS.  */
#ifndef _ALL_SOURCE
# define _ALL_SOURCE 1
#endif
/* Enable extensions on Cosmopolitan Libc. */
#ifndef _COSMO_SOURCE
# define _COSMO_SOURCE 1
#endif
/* Enable general extensions on macOS.  */
#ifndef _DARWIN_C_SOURCE
# define _DARWIN_C_SOURCE 1
#endif
/* Enable general extensions on Solaris.  */
#ifndef __EXTENSIONS__
# define __EXTENSIONS__ 1
#endif
/* Enable GNU extensions on systems that have them.  */
#ifndef _GNU_SOURCE
# define _GNU_SOURCE 1
#endif
/* Enable X/Open compliant socket functions that do not require linking
   with -lxnet on HP-UX 11.11.  */
#ifndef _HPUX_ALT_XOPEN_SOCKET_API
# define _HPUX_ALT_XOPEN_SOCKET_API 1
#endif
/* Identify the host operating system as Minix.
   This macro does not affect the system headers' behavior.
   A future release of Autoconf may stop defining this macro.  */
#ifndef _MINIX
/* # undef _MINIX */
#endif
/* Enable general extensions on NetBSD.
   Enable NetBSD compatibility extensions on Minix.  */
#ifndef _NETBSD_SOURCE
# define _NETBSD_SOURCE 1
#endif
/* Enable OpenBSD compatibility extensions on NetBSD.
   Oddly enough, this does nothing on OpenBSD.  */
#ifndef _OPENBSD_SOURCE
# define _OPENBSD_SOURCE 1
#endif
/* Define to 1 if needed for POSIX-compatible behavior.  */
#ifndef _POSIX_SOURCE
/* # undef _POSIX_SOURCE */
#endif
/* Define to 2 if needed for POSIX-compatible behavior.  */
#ifndef _POSIX_1_SOURCE
/* # undef _POSIX_1_SOURCE */
#endif
/* Enable POSIX-compatible threading on Solaris.  */
#ifndef _POSIX_PTHREAD_SEMANTICS
# define _POSIX_PTHREAD_SEMANTICS 1
#endif
/* Enable extensions specified by ISO/IEC TS 18661-5:2014.  */
#ifndef __STDC_WANT_IEC_60559_ATTRIBS_EXT__
# define __STDC_WANT_IEC_60559_ATTRIBS_EXT__ 1
#endif
/* Enable extensions specified by ISO/IEC TS 18661-1:2014.  */
#ifndef __STDC_WANT_IEC_60559_BFP_EXT__
# define __STDC_WANT_IEC_60559_BFP_EXT__ 1
#endif
/* Enable extensions specified by ISO/IEC TS 18661-2:2015.  */
#ifndef __STDC_WANT_IEC_60559_DFP_EXT__
# define __STDC_WANT_IEC_60559_DFP_EXT__ 1
#endif
/* Enable extensions specified by C23 Annex F.  */
#ifndef __STDC_WANT_IEC_60559_EXT__
# define __STDC_WANT_IEC_60559_EXT__ 1
#endif
/* Enable extensions specified by ISO/IEC TS 18661-4:2015.  */
#ifndef __STDC_WANT_IEC_60559_FUNCS_EXT__
# define __STDC_WANT_IEC_60559_FUNCS_EXT__ 1
#endif
/* Enable extensions specified by C23 Annex H and ISO/IEC TS 18661-3:2015.  */
#ifndef __STDC_WANT_IEC_60559_TYPES_EXT__
# define __STDC_WANT_IEC_60559_TYPES_EXT__ 1
#endif
/* Enable extensions specified by ISO/IEC TR 24731-2:2010.  */
#ifndef __STDC_WANT_LIB_EXT2__
# define __STDC_WANT_LIB_EXT2__ 1
#endif
/* Enable extensions specified by ISO/IEC 24747:2009.  */
#ifndef __STDC_WANT_MATH_SPEC_FUNCS__
# define __STDC_WANT_MATH_SPEC_FUNCS__ 1
#endif
/* Enable extensions on HP NonStop.  */
#ifndef _TANDEM_SOURCE
# define _TANDEM_SOURCE 1
#endif
/* Enable X/Open extensions.  Define to 500 only if necessary
   to make mbstate_t available.  */
#ifndef _XOPEN_SOURCE
/* # undef _XOPEN_SOURCE */
#endif


/* Version number of package */
#define VERSION "1.22-devel"

/* Path to xmllint program for tests */
#define XMLLINT_PATH "/usr/bin/xmllint"

/* Define to 1 if 'lex' declares 'yytext' as a 'char *' by default, not a
   'char[]'. */
#define YYTEXT_POINTER 1

/* Define to '__inline__' or '__inline' if that's what the C compiler
   calls it, or to nothing if 'inline' is not supported under any name.  */
#ifndef __cplusplus
/* #undef inline */
#endif

/* Define to the equivalent of the C99 'restrict' keyword, or to
   nothing if this is not supported.  Do not define if restrict is
   supported only directly.  */
#define restrict __restrict__
/* Work around a bug in older versions of Sun C++, which did not
   #define __restrict__ or support _Restrict or __restrict__
   even though the corresponding Sun C compiler ended up with
   "#define restrict _Restrict" or "#define restrict __restrict__"
   in the previous line.  This workaround can be removed once
   we assume Oracle Developer Studio 12.5 (2016) or later.  */
#if defined __SUNPRO_CC && !defined __RESTRICT && !defined __restrict__
# define _Restrict
# define __restrict__
#endif
