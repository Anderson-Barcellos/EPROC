"""
### 🐛 Custom Traceback Formatter
Enhanced traceback formatting for better terminal output readability and bug line detection.
This module provides a project-wide solution for formatting errors in a more organized and directive manner.
Uses extensive sys module features for better Python integration.
"""

import traceback
import sys
import os
import inspect
from typing import List, Dict, Optional, Tuple, Any, TextIO
from pathlib import Path
import re
from colorama import Fore, Back, Style, init
import threading
import atexit

# Initialize colorama for cross-platform colored output
init(autoreset=True)

#■■■■■■■■■■■
# SYSTEM INTEGRATION UTILITIES
#■■■■■■■■■■■

class SystemTracebackManager:
    """
    ### 🔧 System Traceback Manager
    Manages system-level traceback hooks and settings using sys module extensively.
    """

    def __init__(self):
        self._original_excepthook = sys.excepthook
        self._original_stderr = sys.stderr
        self._original_tracebacklimit = getattr(sys, 'tracebacklimit', 1000)
        self._custom_formatter = None
        self._lock = threading.Lock()

        # Register cleanup on exit
        atexit.register(self.restore_system_defaults)

    def install_custom_hook(self, formatter: 'CustomTracebackFormatter'):
        """Install custom exception hook with thread safety."""
        with self._lock:
            self._custom_formatter = formatter
            sys.excepthook = self._custom_exception_handler

            # Adjust traceback limit for better context
            sys.tracebacklimit = max(formatter.show_context_lines * 2, 50)

    def _custom_exception_handler(self, exc_type, exc_value, exc_traceback):
        """Custom exception handler using sys integration."""
        # Don't format KeyboardInterrupt and SystemExit
        if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
            self._original_excepthook(exc_type, exc_value, exc_traceback)
            return

        if self._custom_formatter:
            self._custom_formatter.format_exception(exc_type, exc_value, exc_traceback)
        else:
            self._original_excepthook(exc_type, exc_value, exc_traceback)

    def restore_system_defaults(self):
        """Restore original system settings."""
        with self._lock:
            sys.excepthook = self._original_excepthook
            sys.stderr = self._original_stderr
            sys.tracebacklimit = self._original_tracebacklimit
            print("🔄 Sistema de traceback restaurado aos padrões originais")

# Global manager instance
_system_manager = SystemTracebackManager()

#■■■■■■■■■■■
# TRACEBACK FORMATTER CLASS
#■■■■■■■■■■■

class CustomTracebackFormatter:
    """
    ### 🔧 Custom Traceback Formatter
    A comprehensive traceback formatter that provides enhanced error visualization with
    improved readability, context highlighting, and bug line detection capabilities.

    Enhanced with extensive sys module integration for better Python compatibility.

    ### 🖥️ Parameters
        - `show_locals` (`bool`, optional): Whether to display local variables in the error context. Defaults to `False`.
        - `show_context_lines` (`int`, optional): Number of context lines to show around the error. Defaults to `3`.
        - `highlight_keywords` (`List[str]`, optional): Keywords to highlight in the traceback. Defaults to common error patterns.
        - `project_root` (`str`, optional): Project root directory for relative path display. Defaults to current working directory.
        - `enable_colors` (`bool`, optional): Whether to use colored output. Defaults to `True`.
        - `output_stream` (`TextIO`, optional): Output stream for errors. Defaults to `sys.stderr`.
        - `max_traceback_depth` (`int`, optional): Maximum traceback depth. Defaults to `sys.tracebacklimit`.

    ### 🔄 Returns
        - Instance of CustomTracebackFormatter ready for use.

    ### 💡 Example

    >>> formatter = CustomTracebackFormatter(show_locals=True, show_context_lines=5)
    >>> try:
    ...     risky_operation()
    ... except Exception as e:
    ...     formatter.format_exception()

    ### 📚 Notes
    - Integrates deeply with sys module for better Python compatibility
    - Automatically detects project files vs. system/library files
    - Provides enhanced context around error lines
    - Supports both terminal and file output with proper stream handling
    """

    def __init__(
        self,
        show_locals: bool = False,
        show_context_lines: int = 3,
        highlight_keywords: Optional[List[str]] = None,
        project_root: Optional[str] = None,
        enable_colors: bool = True,
        output_stream: Optional[TextIO] = None,
        max_traceback_depth: Optional[int] = None
    ):
        self.show_locals = show_locals
        self.show_context_lines = show_context_lines
        self.enable_colors = enable_colors
        self.project_root = Path(project_root or os.getcwd())

        # Use sys for output stream management
        self.output_stream = output_stream or sys.stderr
        self.max_traceback_depth = max_traceback_depth or getattr(sys, 'tracebacklimit', 1000)

        # Default keywords that commonly indicate problematic areas
        self.highlight_keywords = highlight_keywords or [
            'None', 'null', 'undefined', 'empty', 'missing', 'invalid',
            'error', 'fail', 'exception', 'break', 'stop', 'exit'
        ]

        # Color schemes
        self.colors = {
            'error': Fore.RED + Style.BRIGHT,
            'warning': Fore.YELLOW + Style.BRIGHT,
            'info': Fore.BLUE + Style.BRIGHT,
            'success': Fore.GREEN + Style.BRIGHT,
            'highlight': Back.YELLOW + Fore.BLACK,
            'line_number': Fore.CYAN,
            'file_path': Fore.MAGENTA,
            'function_name': Fore.GREEN,
            'variable': Fore.BLUE,
            'reset': Style.RESET_ALL
        }

        # Thread information
        self.thread_id = threading.get_ident()
        self.thread_name = threading.current_thread().name

    def _write_to_stream(self, text: str):
        """Write to output stream with proper error handling."""
        try:
            self.output_stream.write(text + '\n')
            self.output_stream.flush()
        except Exception:
            # Fallback to sys.stderr if current stream fails
            sys.stderr.write(text + '\n')
            sys.stderr.flush()

    def _colorize(self, text: str, color_key: str) -> str:
        """Apply color formatting if colors are enabled."""
        if not self.enable_colors:
            return text
        return f"{self.colors.get(color_key, '')}{text}{self.colors['reset']}"

    def _get_relative_path(self, file_path: str) -> str:
        """Convert absolute path to relative path from project root."""
        try:
            path_obj = Path(file_path)
            if path_obj.is_absolute():
                try:
                    return str(path_obj.relative_to(self.project_root))
                except ValueError:
                    # Path is not relative to project root
                    return str(path_obj)
            return file_path
        except Exception:
            return file_path

    def _is_project_file(self, file_path: str) -> bool:
        """Determine if the file is part of the project (not system/library code)."""
        try:
            path_obj = Path(file_path)
            resolved_path = str(path_obj.resolve())
            project_path = str(self.project_root.resolve())

            # Check if it's in project directory
            if project_path in resolved_path:
                return True

            # Check if it's not in system paths
            system_paths = [
                sys.prefix,
                sys.exec_prefix,
                getattr(sys, 'base_prefix', sys.prefix),
                getattr(sys, 'base_exec_prefix', sys.exec_prefix)
            ]

            for sys_path in system_paths:
                if sys_path and sys_path in resolved_path:
                    return False

            return True

        except Exception:
            return False

    def _get_code_context(self, file_path: str, line_number: int) -> List[Tuple[int, str, bool]]:
        """
        Get code context around the error line.

        Returns list of tuples: (line_num, line_content, is_error_line)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            start_line = max(0, line_number - self.show_context_lines - 1)
            end_line = min(len(lines), line_number + self.show_context_lines)

            context = []
            for i in range(start_line, end_line):
                line_num = i + 1
                line_content = lines[i].rstrip('\n')
                is_error_line = (line_num == line_number)
                context.append((line_num, line_content, is_error_line))

            return context

        except Exception as read_error:
            return [(line_number, f"Could not read file: {str(read_error)}", True)]

    def _highlight_keywords(self, text: str) -> str:
        """Highlight specific keywords in the text."""
        if not self.enable_colors:
            return text

        highlighted_text = text
        for keyword in self.highlight_keywords:
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            highlighted_text = pattern.sub(
                lambda m: self._colorize(m.group(), 'highlight'),
                highlighted_text
            )
        return highlighted_text

    def _format_local_variables(self, frame_locals: Dict[str, Any]) -> str:
        """Format local variables for display."""
        if not frame_locals:
            return ""

        output = ["\n" + "─" * 50]
        output.append(self._colorize("🔍 LOCAL VARIABLES:", 'info'))
        output.append("─" * 50)

        for var_name, var_value in frame_locals.items():
            # Skip internal/private variables
            if var_name.startswith('_'):
                continue

            try:
                # Limit string representation length
                str_value = str(var_value)
                if len(str_value) > 100:
                    str_value = str_value[:97] + "..."

                var_line = f"  {self._colorize(var_name, 'variable')}: {str_value}"
                output.append(var_line)
            except Exception:
                output.append(f"  {self._colorize(var_name, 'variable')}: <unable to display>")

        output.append("─" * 50)
        return "\n".join(output)

    def _get_system_info(self) -> str:
        """Get system and thread information."""
        info_lines = [
            f"🐍 Python: {sys.version.split()[0]}",
            f"🖥️ Platform: {sys.platform}",
            f"🧵 Thread: {self.thread_name} (ID: {self.thread_id})",
            f"📁 Working Dir: {os.getcwd()}",
            f"🔢 Traceback Limit: {sys.tracebacklimit}"
        ]
        return " | ".join(info_lines)

    def format_exception(
        self,
        exc_type: type = None,
        exc_value: Exception = None,
        exc_traceback = None,
        output_file: Optional[str] = None
    ) -> str:
        """
        ### 🎯 Format Exception
        Main method to format exceptions with enhanced readability and context.
        Now with improved sys module integration.

        ### 🖥️ Parameters
            - `exc_type` (`type`, optional): Exception type. If None, uses current exception from sys.exc_info().
            - `exc_value` (`Exception`, optional): Exception instance. If None, uses current exception from sys.exc_info().
            - `exc_traceback` (optional): Traceback object. If None, uses current exception from sys.exc_info().
            - `output_file` (`str`, optional): File path to write the formatted output. If None, prints to configured stream.

        ### 🔄 Returns
            - `str`: The formatted traceback string.

        ### ⚠️ Raises
            - `ValueError`: If no exception information is available.

        ### 💡 Example

        >>> try:
        ...     problematic_function()
        ... except Exception:
        ...     formatter.format_exception()
        """

        # Get current exception info if not provided - using sys.exc_info()
        if exc_type is None or exc_value is None or exc_traceback is None:
            exc_type, exc_value, exc_traceback = sys.exc_info() # type: ignore

        if exc_type is None:
            raise ValueError("No exception information available. Use within except block or provide exception details.")

        # Build the formatted output
        output_lines = []

        # Header with system information
        output_lines.extend([
            "\n" + "■" * 80,
            self._colorize("🚨 ENHANCED ERROR REPORT", 'error'),
            "■" * 80,
            f"📅 Timestamp: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"🔥 Exception Type: {self._colorize(exc_type.__name__, 'error')}",
            f"💬 Message: {self._colorize(str(exc_value), 'error')}",
            f"📊 System Info: {self._get_system_info()}",
            "■" * 80
        ])

        # Process traceback with depth limit
        tb_list = traceback.extract_tb(exc_traceback, limit=self.max_traceback_depth)

        output_lines.append(self._colorize("📍 TRACEBACK ANALYSIS:", 'info'))
        output_lines.append("-" * 80)

        for i, frame in enumerate(tb_list):
            file_path = frame.filename
            line_number = frame.lineno
            function_name = frame.name
            code_line = frame.line or "<unavailable>"

            # Format frame header
            relative_path = self._get_relative_path(file_path)
            is_project = self._is_project_file(file_path)

            frame_marker = "🔴" if is_project else "🔵"
            file_type = "PROJECT FILE" if is_project else "SYSTEM/LIBRARY"

            output_lines.extend([
                f"\n{frame_marker} Frame {i + 1} - {file_type}",
                f"📁 File: {self._colorize(relative_path, 'file_path')}",
                f"🎯 Function: {self._colorize(function_name, 'function_name')}",
                f"📏 Line: {self._colorize(str(line_number), 'line_number')}"
            ])

            # Show code context for project files
            if is_project and os.path.exists(file_path):
                context = self._get_code_context(file_path, line_number)

                output_lines.append("\n🔍 CODE CONTEXT:")
                for line_num, line_content, is_error_line in context:
                    marker = ">>>" if is_error_line else "   "
                    line_color = 'error' if is_error_line else 'reset'

                    formatted_line = f"{marker} {line_num:4d} | {line_content}"
                    if is_error_line:
                        formatted_line = self._colorize(formatted_line, line_color)
                        formatted_line = self._highlight_keywords(formatted_line)

                    output_lines.append(formatted_line)

            # Show local variables if requested and it's a project frame
            if self.show_locals and is_project:
                try:
                    # Get frame object to access locals using sys-compatible approach
                    current_frame = exc_traceback
                    for _ in range(i):
                        if current_frame.tb_next:
                            current_frame = current_frame.tb_next

                    if current_frame and current_frame.tb_frame:
                        locals_output = self._format_local_variables(current_frame.tb_frame.f_locals)
                        if locals_output:
                            output_lines.append(locals_output)
                except Exception as e:
                    output_lines.append(f"⚠️ Could not retrieve local variables: {str(e)}")

            output_lines.append("-" * 80)

        # Summary and suggestions
        output_lines.extend([
            "",
            self._colorize("💡 DEBUGGING SUGGESTIONS:", 'info'),
            "- Check the highlighted lines marked with '>>>' for potential issues",
            "- Look for variables with None, empty, or unexpected values",
            "- Verify input parameters and their types",
            "- Consider adding defensive programming checks",
            "- Use debugger or print statements around the error location",
            f"- Current Python path: {sys.executable}",
            f"- Use sys.settrace() for advanced debugging if needed",
            "■" * 80
        ])

        formatted_output = "\n".join(output_lines)

        # Output handling with proper stream management
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    # Remove color codes for file output
                    clean_output = re.sub(r'\x1b\[[0-9;]*m', '', formatted_output)
                    f.write(clean_output)
                self._write_to_stream(f"📝 Formatted traceback saved to: {output_file}")
            except Exception as e:
                self._write_to_stream(f"⚠️ Could not write to file {output_file}: {str(e)}")

        self._write_to_stream(formatted_output)
        return formatted_output

#■■■■■■■■■■■
# UTILITY FUNCTIONS WITH SYS INTEGRATION
#■■■■■■■■■■■

def setup_global_exception_handler(formatter: Optional[CustomTracebackFormatter] = None):
    """
    ### 🌍 Setup Global Exception Handler
    Configure a global exception handler using the custom traceback formatter.
    Now with enhanced sys module integration.

    ### 🖥️ Parameters
        - `formatter` (`CustomTracebackFormatter`, optional): Custom formatter instance.
          If None, creates a default formatter.

    ### 💡 Example

    >>> setup_global_exception_handler()
    >>> # Now all unhandled exceptions will use the custom formatter
    """
    if formatter is None:
        formatter = CustomTracebackFormatter()

    _system_manager.install_custom_hook(formatter)
    print("🔧 Global exception handler configured with enhanced sys integration")

def restore_system_defaults():
    """
    ### 🔄 Restore System Defaults
    Restore original system exception handling and settings.

    ### 💡 Example

    >>> restore_system_defaults()
    >>> # System traceback behavior restored
    """
    _system_manager.restore_system_defaults()

def format_current_exception(
    show_locals: bool = False,
    show_context_lines: int = 3,
    output_file: Optional[str] = None,
    output_stream: Optional[TextIO] = None
) -> str:
    """
    ### ⚡ Format Current Exception
    Convenience function to format the current exception using default settings.
    Enhanced with sys module integration.

    ### 🖥️ Parameters
        - `show_locals` (`bool`, optional): Whether to show local variables. Defaults to `False`.
        - `show_context_lines` (`int`, optional): Number of context lines. Defaults to `3`.
        - `output_file` (`str`, optional): File to save output. Defaults to `None`.
        - `output_stream` (`TextIO`, optional): Output stream. Defaults to `sys.stderr`.

    ### 🔄 Returns
        - `str`: Formatted traceback string.

    ### 💡 Example

    >>> try:
    ...     problematic_code()
    ... except Exception:
    ...     format_current_exception(show_locals=True, output_file="error_log.txt")
    """
    formatter = CustomTracebackFormatter(
        show_locals=show_locals,
        show_context_lines=show_context_lines,
        output_stream=output_stream or sys.stderr
    )
    return formatter.format_exception(output_file=output_file)

def set_traceback_limit(limit: int):
    """
    ### 📏 Set Traceback Limit
    Set the maximum number of traceback levels using sys.tracebacklimit.

    ### 🖥️ Parameters
        - `limit` (`int`): Maximum number of traceback levels to display

    ### 💡 Example

    >>> set_traceback_limit(50)  # Show up to 50 frames
    """
    sys.tracebacklimit = limit
    print(f"🔢 Traceback limit set to: {limit}")

def get_current_frame_info() -> Dict[str, Any]:
    """
    ### 🔍 Get Current Frame Info
    Get information about the current execution frame using sys._getframe().

    ### 🔄 Returns
        - `Dict[str, Any]`: Frame information including filename, function, line number

    ### 💡 Example

    >>> info = get_current_frame_info()
    >>> print(f"Currently in: {info['function']} at line {info['lineno']}")
    """
    try:
        frame = sys._getframe(1)  # Get caller's frame
        return {
            'filename': frame.f_code.co_filename,
            'function': frame.f_code.co_name,
            'lineno': frame.f_lineno,
            'locals': dict(frame.f_locals),
            'globals_keys': list(frame.f_globals.keys())
        }
    except Exception as e:
        return {'error': str(e)}

# Context manager for temporary exception formatting with sys integration
class TemporaryTracebackFormatter:
    """
    ### 🔄 Temporary Traceback Formatter
    Context manager for temporarily using custom traceback formatting.
    Enhanced with proper sys module integration.

    ### 💡 Example

    >>> with TemporaryTracebackFormatter(show_locals=True):
    ...     risky_operation()  # Any exception here will use custom formatting
    """

    def __init__(self, **formatter_kwargs):
        self.formatter = CustomTracebackFormatter(**formatter_kwargs)
        self.original_excepthook = None
        self.original_tracebacklimit = None

    def __enter__(self):
        # Store original sys settings
        self.original_excepthook = sys.excepthook
        self.original_tracebacklimit = getattr(sys, 'tracebacklimit', 1000)

        # Install temporary custom handler
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
                self.original_excepthook(exc_type, exc_value, exc_traceback) # type: ignore
                return
            self.formatter.format_exception(exc_type, exc_value, exc_traceback)

        sys.excepthook = handle_exception
        sys.tracebacklimit = max(self.formatter.show_context_lines * 2, 50)

        return self.formatter

    def __exit__(self, exc_type, exc_value, exc_traceback):
        # Restore original sys settings
        sys.excepthook = self.original_excepthook
        sys.tracebacklimit = self.original_tracebacklimit

        if exc_type is not None:
            # Format the exception that caused the context exit
            self.formatter.format_exception(exc_type, exc_value, exc_traceback)
            return True  # Suppress the exception

# Print system info for debugging
def print_system_info():
    """
    ### 📊 Print System Info
    Print comprehensive system information for debugging purposes.
    """
    info_lines = [
        f"🐍 Python Version: {sys.version}",
        f"🖥️ Platform: {sys.platform}",
        f"📁 Python Executable: {sys.executable}",
        f"📦 Python Path: {sys.path[:3]}..." if len(sys.path) > 3 else f"📦 Python Path: {sys.path}",
        f"🔢 Current Traceback Limit: {getattr(sys, 'tracebacklimit', 'unlimited')}",
        f"🧵 Thread Info: {threading.current_thread().name} (ID: {threading.get_ident()})",
        f"💾 Memory Info: {sys.getsizeof(sys.modules)} bytes in modules"
    ]

    print("📊 SYSTEM INFORMATION:")
    print("-" * 50)
    for line in info_lines:
        print(line)
    print("-" * 50)