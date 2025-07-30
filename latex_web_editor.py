import streamlit as st
import subprocess
import tempfile
import os
from PIL import Image
import pdf2image
import re

def compile_latex_to_pdf(latex_code):
    """Compile LaTeX code to PDF"""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            tex_file = os.path.join(temp_dir, "document.tex")
            pdf_file = os.path.join(temp_dir, "document.pdf")
            
            # Write LaTeX file
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_code)
            
            # Compile LaTeX (run twice to ensure references are correct)
            for i in range(2):
                result = subprocess.run(
                    ['pdflatex', '-interaction=nonstopmode', 
                     '-output-directory', temp_dir, tex_file],
                    capture_output=True,
                    text=True,
                    cwd=temp_dir,
                    timeout=30
                )
            
            if result.returncode == 0 and os.path.exists(pdf_file):
                with open(pdf_file, 'rb') as f:
                    return f.read(), None
            else:
                return None, result.stderr or result.stdout
                
    except Exception as e:
        return None, str(e)

def safe_replace_tikz(latex_content, new_tikz_content):
    """Safely replace TikZ content to avoid regex errors"""
    try:
        # Find tikzpicture start and end positions
        start_pattern = r'\\begin\{tikzpicture\}'
        end_pattern = r'\\end\{tikzpicture\}'
        
        start_match = re.search(start_pattern, latex_content)
        if start_match:
            # Search for corresponding end tag from first match
            start_pos = start_match.start()
            remaining_content = latex_content[start_pos:]
            
            end_match = re.search(end_pattern, remaining_content)
            if end_match:
                end_pos = start_pos + end_match.end()
                
                # Build new content
                before = latex_content[:start_pos]
                after = latex_content[end_pos:]
                new_content = before + new_tikz_content + after
                
                return new_content
        
        # If no existing tikzpicture found, add to end of document
        insert_pos = latex_content.rfind("\\end{document}")
        if insert_pos != -1:
            new_content = (latex_content[:insert_pos] + 
                         "\n\\section{New Figure}\n" + 
                         new_tikz_content + "\n\n" + 
                         latex_content[insert_pos:])
        else:
            new_content = latex_content + "\n\n" + new_tikz_content
            
        return new_content
        
    except Exception as e:
        st.error(f"Error replacing TikZ content: {e}")
        return latex_content

def copy_error_to_clipboard(error_message, lines=30):
    """Copy first N lines of error message to clipboard"""
    try:
        import pyperclip
        lines_list = error_message.splitlines()
        head_lines = lines_list[:lines]
        head_text = '\n'.join(head_lines)
        
        if head_text.strip():
            pyperclip.copy(head_text)
            return True, len(head_lines)
        else:
            return False, 0
    except ImportError:
        st.error("Need to install pyperclip: uv add pyperclip")
        return False, 0
    except Exception as e:
        st.error(f"Copy failed: {e}")
        return False, 0

def one_click_paste_and_compile():
    """One-click paste and compile function"""
    try:
        # Read from clipboard
        import pyperclip
        clipboard_content = pyperclip.paste()
        
        if not clipboard_content.strip():
            st.warning("⚠️ Clipboard is empty")
            return False
        
        # Update TikZ editor
        st.session_state.tikz_content = clipboard_content
        
        # Update main LaTeX code
        current_latex = st.session_state.latex_content
        new_latex = safe_replace_tikz(current_latex, clipboard_content)
        st.session_state.latex_content = new_latex
        
        return clipboard_content
        
    except ImportError:
        st.error("❌ Need to install pyperclip package: `uv add pyperclip`")
        return False
    except Exception as e:
        st.error(f"❌ Failed to read clipboard: {e}")
        return False

def main():
    st.set_page_config(
        page_title="LaTeX Editor with TikZ", 
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    st.title("📝 LaTeX Editor with PDF Preview & TikZ Graphics")
    st.markdown("---")
    
    # Initialize session state
    if 'latex_content' not in st.session_state:
        st.session_state.latex_content = r"""\documentclass[12pt]{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath}
\usepackage{amsfonts}
\usepackage{geometry}
\usepackage{tikz}
\usetikzlibrary{positioning,shapes,arrows,decorations.markings}

\geometry{a4paper, margin=2.5cm}

\title{My LaTeX Document}
\author{Author Name}
\date{\today}

\begin{document}

\maketitle

\section{Introduction}
This is a sample LaTeX document created with LaTeX editor, supporting TikZ graphics.

\section{Math Examples}
Einstein's mass-energy equation:
\begin{equation}
E = mc^2
\end{equation}

\section{TikZ Graphics Example}
\begin{tikzpicture}
  \node[circle,draw,fill=blue!20] (A) at (0,0) {A};
  \node[rectangle,draw,fill=green!20] (B) at (2,1.5) {B};
  \draw[->,thick] (A) -- (B) node[midway,above] {arrow};
\end{tikzpicture}

\end{document}"""

    if 'tikz_content' not in st.session_state:
        st.session_state.tikz_content = r"""\begin{tikzpicture}
  \node[circle,draw,fill=blue!20] (A) at (0,0) {A};
  \node[rectangle,draw,fill=green!20] (B) at (2,1.5) {B};
  \draw[->,thick] (A) -- (B) node[midway,above] {arrow};
\end{tikzpicture}"""

    # Error message states
    if 'main_latex_error' not in st.session_state:
        st.session_state.main_latex_error = ""
    
    if 'tikz_error' not in st.session_state:
        st.session_state.tikz_error = ""
    
    if 'clipboard_content' not in st.session_state:
        st.session_state.clipboard_content = ""
    
    if 'one_click_error' not in st.session_state:
        st.session_state.one_click_error = ""
        
    if 'quick_test_error' not in st.session_state:
        st.session_state.quick_test_error = ""
    
    # 🚀 Quick operations area
    st.markdown("### 🚀 Quick Operations")
    col_quick1, col_quick2, col_quick3 = st.columns([1, 1, 2])
    
    with col_quick1:
        one_click_button = st.button("📋⚡ One-Click Paste & Compile", type="primary", key="one_click_magic")
    
    with col_quick2:
        quick_tikz_button = st.button("🎨⚡ Quick TikZ Test", type="secondary", key="quick_tikz_test")
    
    with col_quick3:
        # Error copy buttons for quick operations
        col_quick3_1, col_quick3_2 = st.columns([1, 1])
        
        with col_quick3_1:
            has_one_click_error = bool(st.session_state.one_click_error.strip())
            copy_one_click_error = st.button(
                "📋 Copy One-Click Error",
                key="copy_one_click_error",
                disabled=not has_one_click_error,
                help="Copy One-Click compilation error"
            )
            
            if copy_one_click_error and has_one_click_error:
                success, line_count = copy_error_to_clipboard(st.session_state.one_click_error, 30)
                if success:
                    st.success(f"✅ Copied {line_count} lines to clipboard!")
        
        with col_quick3_2:
            has_quick_test_error = bool(st.session_state.quick_test_error.strip())
            copy_quick_test_error = st.button(
                "📋 Copy Quick Test Error",
                key="copy_quick_test_error", 
                disabled=not has_quick_test_error,
                help="Copy Quick Test compilation error"
            )
            
            if copy_quick_test_error and has_quick_test_error:
                success, line_count = copy_error_to_clipboard(st.session_state.quick_test_error, 30)
                if success:
                    st.success(f"✅ Copied {line_count} lines to clipboard!")
        
        # Test error function
        if st.button("🧪 Test Error Function", key="test_error"):
            st.session_state.main_latex_error = "This is a test error message for main LaTeX\nLine 2 of error\nLine 3 of error"
            st.session_state.tikz_error = "This is a test error message for TikZ\nTikZ Line 2\nTikZ Line 3"
            st.session_state.one_click_error = "This is a test One-Click error\nOne-Click Line 2\nOne-Click Line 3"
            st.session_state.quick_test_error = "This is a test Quick Test error\nQuick Test Line 2\nQuick Test Line 3"
            st.success("✅ Test errors created, check copy buttons")
            st.rerun()
    
    # 🆕 PERSISTENT ERROR DISPLAY SECTION
    st.markdown("### 🚨 Error Messages")
    
    error_displayed = False
    
    # Main LaTeX Error Display
    if st.session_state.main_latex_error.strip():
        st.error("❌ **Main File Compilation Error**")
        with st.expander("🔍 View Main File Error Details", expanded=True):
            # Show first 100 lines to avoid overwhelming display
            error_lines = st.session_state.main_latex_error.splitlines()
            if len(error_lines) > 100:
                st.code('\n'.join(error_lines[:100]), language="text")
                st.info(f"Showing first 100 lines of {len(error_lines)} total lines. Use 'Copy Main File Error' button to get full error.")
            else:
                st.code(st.session_state.main_latex_error, language="text")
        error_displayed = True
    
    # TikZ Error Display
    if st.session_state.tikz_error.strip():
        st.error("❌ **TikZ Compilation Error**")
        with st.expander("🔍 View TikZ Error Details", expanded=True):
            error_lines = st.session_state.tikz_error.splitlines()
            if len(error_lines) > 100:
                st.code('\n'.join(error_lines[:100]), language="text")
                st.info(f"Showing first 100 lines of {len(error_lines)} total lines. Use 'Copy TikZ Error' button to get full error.")
            else:
                st.code(st.session_state.tikz_error, language="text")
        error_displayed = True
    
    # One-Click Error Display
    if st.session_state.one_click_error.strip():
        st.error("❌ **One-Click Compilation Error**")
        with st.expander("🔍 View One-Click Error Details", expanded=True):
            error_lines = st.session_state.one_click_error.splitlines()
            if len(error_lines) > 100:
                st.code('\n'.join(error_lines[:100]), language="text")
                st.info(f"Showing first 100 lines of {len(error_lines)} total lines. Use 'Copy One-Click Error' button to get full error.")
            else:
                st.code(st.session_state.one_click_error, language="text")
        error_displayed = True
    
    # Quick Test Error Display
    if st.session_state.quick_test_error.strip():
        st.error("❌ **Quick Test Compilation Error**")
        with st.expander("🔍 View Quick Test Error Details", expanded=True):
            error_lines = st.session_state.quick_test_error.splitlines()
            if len(error_lines) > 100:
                st.code('\n'.join(error_lines[:100]), language="text")
                st.info(f"Showing first 100 lines of {len(error_lines)} total lines. Use 'Copy Quick Test Error' button to get full error.")
            else:
                st.code(st.session_state.quick_test_error, language="text")
        error_displayed = True
    
    if not error_displayed:
        st.success("✅ No compilation errors")
    
    # Clear all errors button
    if error_displayed:
        if st.button("🗑️ Clear All Error Messages", key="clear_all_errors"):
            st.session_state.main_latex_error = ""
            st.session_state.tikz_error = ""
            st.session_state.one_click_error = ""
            st.session_state.quick_test_error = ""
            st.success("All error messages cleared!")
            st.rerun()
    
    # One-click magic button
    if one_click_button:
        with st.spinner("🔄 Executing one-click operation..."):
            clipboard_content = one_click_paste_and_compile()
            
            if clipboard_content:
                # Create standalone LaTeX document
                tikz_latex = "\\documentclass{standalone}\n"
                tikz_latex += "\\usepackage{tikz}\n"
                tikz_latex += "\\usetikzlibrary{positioning,shapes,arrows,decorations.markings,patterns,calc}\n"
                tikz_latex += "\\begin{document}\n"
                tikz_latex += clipboard_content + "\n"
                tikz_latex += "\\end{document}"
                
                pdf_data, error = compile_latex_to_pdf(tikz_latex)
                
                if pdf_data:
                    st.success("✅ One-click operation completed!")
                    st.session_state.one_click_error = ""  # Clear previous errors
                    
                    col_result1, col_result2 = st.columns([1, 1])
                    
                    with col_result1:
                        st.markdown("**🖼️ TikZ Graphics Preview**")
                        try:
                            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                                tmp.write(pdf_data)
                                tmp_path = tmp.name
                            
                            images = pdf2image.convert_from_path(tmp_path, dpi=200)
                            if images:
                                st.image(images, caption="TikZ Graphics", use_column_width=True)
                            
                            os.unlink(tmp_path)
                            
                        except Exception as e:
                            st.warning(f"⚠️ Cannot display preview: {e}")
                    
                    with col_result2:
                        st.markdown("**📄 Pasted Code**")
                        st.code(clipboard_content, language="latex")
                        
                        st.download_button(
                            label="📥 Download TikZ Figure",
                            data=pdf_data,
                            file_name="tikz_figure.pdf",
                            mime="application/pdf",
                            type="secondary"
                        )
                    
                    st.rerun()  # Reload to clear error display
                
                else:
                    # Store error and reload to show it
                    st.session_state.one_click_error = error if error else "Unknown error"
                    st.rerun()
    
    # Quick TikZ test
    if quick_tikz_button:
        with st.spinner("🔄 Quick testing current TikZ..."):
            current_tikz = st.session_state.tikz_content
            if current_tikz.strip():
                # Create standalone LaTeX document
                tikz_latex = "\\documentclass{standalone}\n"
                tikz_latex += "\\usepackage{tikz}\n"
                tikz_latex += "\\usetikzlibrary{positioning,shapes,arrows,decorations.markings,patterns,calc}\n"
                tikz_latex += "\\begin{document}\n"
                tikz_latex += current_tikz + "\n"
                tikz_latex += "\\end{document}"
                
                pdf_data, error = compile_latex_to_pdf(tikz_latex)
                
                if pdf_data:
                    st.success("✅ Quick test completed!")
                    st.session_state.quick_test_error = ""  # Clear previous errors
                    
                    try:
                        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                            tmp.write(pdf_data)
                            tmp_path = tmp.name
                        
                        images = pdf2image.convert_from_path(tmp_path, dpi=200)
                        if images:
                            st.image(images, caption="Quick TikZ Test Result", use_column_width=True)
                        
                        os.unlink(tmp_path)
                        
                    except Exception as e:
                        st.warning(f"⚠️ Cannot display preview: {e}")
                    
                    st.rerun()  # Reload to clear error display
                else:
                    # Store error and reload to show it
                    st.session_state.quick_test_error = error if error else "Unknown error"
                    st.rerun()
            else:
                st.warning("⚠️ TikZ editor is empty")
    
    st.markdown("---")
    
    # Create three-column layout
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.header("📄 Main LaTeX Code")
        
        # LaTeX editor
        latex_code = st.text_area(
            "Enter LaTeX code:",
            value=st.session_state.latex_content,
            height=400,
            key="latex_editor"
        )
        
        # Update session state
        if latex_code != st.session_state.latex_content:
            st.session_state.latex_content = latex_code
        
        # First row buttons
        col1_1, col1_2 = st.columns([1, 1])
        
        with col1_1:
            compile_button = st.button("🔄 Compile PDF", type="primary", key="compile_main")
        
        with col1_2:
            if st.button("🗑️ Clear Main File", key="clear_main"):
                st.session_state.latex_content = ""
                st.session_state.main_latex_error = ""
                st.rerun()
        
        # Second row: error copy buttons
        has_main_error = bool(st.session_state.main_latex_error.strip())
        
        col1_3, col1_4 = st.columns([1, 1])
        
        with col1_3:
            copy_main_error_button = st.button(
                "📋 Copy Main File Error", 
                key="copy_main_error", 
                disabled=not has_main_error,
                help=f"Copy first 30 lines of main LaTeX compilation error ({len(st.session_state.main_latex_error)} chars)" if has_main_error else "No main file compilation error"
            )
        
        with col1_4:
            if has_main_error:
                st.write("🔴 Main file has error")
                st.caption(f"Error length: {len(st.session_state.main_latex_error)} chars")
            else:
                st.write("🟢 Main file no error")
        
        # Handle copy main file error button
        if copy_main_error_button:
            if st.session_state.main_latex_error.strip():
                success, line_count = copy_error_to_clipboard(st.session_state.main_latex_error, 30)
                if success:
                    st.success(f"✅ Copied first {line_count} lines of main file error to clipboard!")
                else:
                    st.error("❌ Failed to copy main file error message")
            else:
                st.warning("⚠️ No error message to copy")
        
        # Compile main file
        if compile_button:
            if not latex_code.strip():
                st.warning("⚠️ Please enter LaTeX code")
            else:
                with st.spinner("🔄 Compiling main file..."):
                    pdf_data, error = compile_latex_to_pdf(latex_code)
                    
                    if pdf_data:
                        st.success("✅ Compilation successful!")
                        st.session_state.main_latex_error = ""
                        
                        # Provide download button
                        st.download_button(
                            label="📥 Download Complete PDF",
                            data=pdf_data,
                            file_name="document.pdf",
                            mime="application/pdf",
                            type="secondary"
                        )
                        
                        # Display PDF preview
                        try:
                            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                                tmp.write(pdf_data)
                                tmp_path = tmp.name
                            
                            images = pdf2image.convert_from_path(tmp_path, dpi=150)
                            if images:
                                st.image(images, caption="Main File PDF Preview", use_column_width=True)
                            
                            os.unlink(tmp_path)
                            
                        except Exception as e:
                            st.warning(f"⚠️ Cannot display preview: {e}")
                        
                        st.rerun()  # Reload to update error display
                            
                    else:
                        st.error("❌ Main file compilation failed!")
                        error_message = error if error and error.strip() else "Unknown compilation error"
                        st.session_state.main_latex_error = error_message
                        
                        st.info(f"💡 Error message saved ({len(error_message)} chars) - Check 'Error Messages' section above")
                        
                        # Only reload on error to update error display
                        st.rerun()
    
    with col2:
        st.header("🖼️ TikZ Graphics Test Area")
        
        # TikZ editor
        tikz_code = st.text_area(
            "Enter TikZ graphics code:",
            value=st.session_state.tikz_content,
            height=200,
            key="tikz_editor"
        )
        
        # Update session state
        if tikz_code != st.session_state.tikz_content:
            st.session_state.tikz_content = tikz_code
        
        # TikZ test buttons
        col2_1, col2_2 = st.columns([1, 1])
        
        with col2_1:
            test_tikz_button = st.button("🎨 Test TikZ", type="primary", key="test_tikz")
        
        with col2_2:
            if st.button("🗑️ Clear TikZ", key="clear_tikz"):
                st.session_state.tikz_content = ""
                st.session_state.tikz_error = ""
                st.rerun()
        
        # TikZ error copy button
        has_tikz_error = bool(st.session_state.tikz_error.strip())
        
        col2_3, col2_4 = st.columns([1, 1])
        
        with col2_3:
            copy_tikz_error_button = st.button(
                "📋 Copy TikZ Error", 
                key="copy_tikz_error", 
                disabled=not has_tikz_error,
                help=f"Copy first 30 lines of TikZ compilation error ({len(st.session_state.tikz_error)} chars)" if has_tikz_error else "No TikZ compilation error"
            )
        
        with col2_4:
            if has_tikz_error:
                st.write("🔴 TikZ has error")
                st.caption(f"Error length: {len(st.session_state.tikz_error)} chars")
            else:
                st.write("🟢 TikZ no error")
        
        # Handle copy TikZ error button
        if copy_tikz_error_button:
            if st.session_state.tikz_error.strip():
                success, line_count = copy_error_to_clipboard(st.session_state.tikz_error, 30)
                if success:
                    st.success(f"✅ Copied first {line_count} lines of TikZ error to clipboard!")
                else:
                    st.error("❌ Failed to copy TikZ error message")
            else:
                st.warning("⚠️ No error message to copy")
        
        if test_tikz_button:
            if not tikz_code.strip():
                st.warning("⚠️ Please enter TikZ code")
            else:
                with st.spinner("🔄 Compiling TikZ graphics..."):
                    # Create standalone TikZ file
                    tikz_latex = "\\documentclass{standalone}\n"
                    tikz_latex += "\\usepackage{tikz}\n"
                    tikz_latex += "\\usetikzlibrary{positioning,shapes,arrows,decorations.markings,patterns,calc}\n"
                    tikz_latex += "\\begin{document}\n"
                    tikz_latex += tikz_code + "\n"
                    tikz_latex += "\\end{document}"
                    
                    pdf_data, error = compile_latex_to_pdf(tikz_latex)
                    
                    if pdf_data:
                        st.success("✅ TikZ graphics compilation successful!")
                        st.session_state.tikz_error = ""
                        
                        # Provide download button
                        st.download_button(
                            label="📥 Download TikZ Figure",
                            data=pdf_data,
                            file_name="tikz_figure.pdf",
                            mime="application/pdf",
                            type="secondary"
                        )
                        
                        # Display TikZ preview
                        try:
                            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                                tmp.write(pdf_data)
                                tmp_path = tmp.name
                            
                            images = pdf2image.convert_from_path(tmp_path, dpi=200)
                            if images:
                                st.image(images, caption="TikZ Graphics Preview", use_column_width=True)
                            
                            os.unlink(tmp_path)
                            
                        except Exception as e:
                            st.warning(f"⚠️ Cannot display TikZ preview: {e}")
                        
                        st.rerun()  # Reload to update error display
                            
                    else:
                        st.error("❌ TikZ compilation failed!")
                        error_message = error if error and error.strip() else "Unknown TikZ compilation error"
                        st.session_state.tikz_error = error_message
                        
                        st.info(f"💡 TikZ error message saved ({len(error_message)} chars) - Check 'Error Messages' section above")
                        
                        # Only reload on error
                        st.rerun()
        
        # TikZ examples
        with st.expander("💡 TikZ Code Examples"):
            st.code("""
# Basic nodes and arrows
\\begin{tikzpicture}
  \\node[circle,draw] (A) at (0,0) {A};
  \\node[rectangle,draw] (B) at (2,0) {B};
  \\draw[->] (A) -- (B);
\\end{tikzpicture}

# Flowchart using positioning library
\\begin{tikzpicture}
  \\node[draw,rounded corners] (start) {Start};
  \\node[draw,below=of start] (process) {Process};
  \\node[draw,diamond,below=of process] (decision) {Decision?};
  \\draw[->] (start) -- (process);
  \\draw[->] (process) -- (decision);
\\end{tikzpicture}

# Mathematical plot
\\begin{tikzpicture}
  \\draw[->] (-2,0) -- (2,0) node[right] {$x$};
  \\draw[->] (0,-1) -- (0,2) node[above] {$y$};
  \\draw[domain=-1.5:1.5,blue] plot (\\x,{\\x*\\x});
\\end{tikzpicture}
            """, language="latex")
    
    with col3:
        st.header("📋 Clipboard Functions")
        
        st.markdown("**Manual Operation Mode**")
        
        # Display clipboard content input box
        clipboard_input = st.text_area(
            "Or directly input TikZ code here:",
            value=st.session_state.clipboard_content,
            height=150,
            key="clipboard_input",
            placeholder="Paste TikZ code here"
        )
        
        # Button row
        col3_1, col3_2 = st.columns([1, 1])
        
        with col3_1:
            paste_button = st.button("📋 Read Clipboard", key="paste_clipboard")
        
        with col3_2:
            apply_button = st.button("✅ Apply to Editor", type="primary", key="apply_tikz")
        
        # Read from clipboard
        if paste_button:
            try:
                import pyperclip
                clipboard_content = pyperclip.paste()
                
                if clipboard_content:
                    st.session_state.clipboard_content = clipboard_content
                    st.success("✅ Content read from clipboard!")
                    st.rerun()
                else:
                    st.warning("⚠️ Clipboard is empty")
                    
            except ImportError:
                st.error("❌ Need to install pyperclip package: `uv add pyperclip`")
            except Exception as e:
                st.error(f"❌ Failed to read clipboard: {e}")
        
        # Apply to editor
        if apply_button:
            tikz_content = clipboard_input.strip()
            if tikz_content:
                # Update TikZ editor
                st.session_state.tikz_content = tikz_content
                
                # Use safe replace function to update main LaTeX code
                current_latex = st.session_state.latex_content
                new_latex = safe_replace_tikz(current_latex, tikz_content)
                st.session_state.latex_content = new_latex
                st.session_state.clipboard_content = ""  # Clear input box
                
                st.success("✅ TikZ code applied to editor!")
                st.info("Please click corresponding compile button to view results")
                st.rerun()
            else:
                st.warning("⚠️ No content to apply")
        
        # Quick TikZ templates
        st.markdown("**Quick TikZ Templates**")
        
        template_options = {
            "Basic Nodes": r"""\begin{tikzpicture}
  \node[circle,draw,fill=blue!20] (A) at (0,0) {A};
  \node[rectangle,draw,fill=red!20] (B) at (2,0) {B};
  \draw[->] (A) -- (B);
\end{tikzpicture}""",
            "Flowchart (positioning)": r"""\begin{tikzpicture}
  \node[draw,rounded corners] (start) {Start};
  \node[draw,below=of start] (process) {Process};
  \node[draw,diamond,below=of process] (decision) {Decision?};
  \node[draw,rounded corners,below=of decision] (end) {End};
  \draw[->] (start) -- (process);
  \draw[->] (process) -- (decision);
  \draw[->] (decision) -- (end);
\end{tikzpicture}""",
            "Math Function": r"""\begin{tikzpicture}
  \draw[->] (-2,0) -- (2,0) node[right] {$x$};
  \draw[->] (0,-1) -- (0,2) node[above] {$y$};
  \draw[domain=-1.5:1.5,blue,thick] plot (\x,{\x*\x});
  \node at (1,1.5) {$y=x^2$};
\end{tikzpicture}""",
            "Your Example": r"""\begin{tikzpicture}
  \node[circle,draw,fill=blue!20] (A) at (0,0) {A};
  \node[rectangle,draw,fill=green!20] (B) at (2,1.5) {B};
  \draw[->,thick] (A) -- (B) node[midway,above] {arrow};
\end{tikzpicture}"""
        }
        
        selected_template = st.selectbox("Select template:", list(template_options.keys()))
        
        if st.button("📝 Load Template", key="load_template"):
            st.session_state.clipboard_content = template_options[selected_template]
            st.success(f"✅ {selected_template} template loaded to input box")
            st.rerun()

if __name__ == "__main__":
    main()
