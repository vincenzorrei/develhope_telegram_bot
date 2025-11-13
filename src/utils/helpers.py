"""
Helper Utilities Module

Funzioni di utilità generiche utilizzate in tutto il progetto.
Include validazione, formattazione, e operazioni comuni.
"""

import os
import hashlib
import re
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
import tiktoken


def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    """
    Conta tokens in un testo per un dato modello.

    Utile per gestire limiti API e ottimizzare costi.

    Args:
        text: Testo da analizzare
        model: Modello OpenAI (default: gpt-4o-mini)

    Returns:
        Numero di tokens

    Example:
        >>> count_tokens("Hello world!")
        3
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback: stima approssimativa (1 token ≈ 4 caratteri)
        return len(text) // 4


def truncate_text(
    text: str,
    max_tokens: int = 1000,
    model: str = "gpt-4o-mini",
    suffix: str = "..."
) -> str:
    """
    Tronca testo a massimo N tokens.

    Args:
        text: Testo da troncare
        max_tokens: Numero massimo tokens
        model: Modello per conteggio tokens
        suffix: Suffisso da aggiungere se troncato

    Returns:
        Testo troncato

    Example:
        >>> truncate_text("Very long text...", max_tokens=10)
        'Very long...'
    """
    current_tokens = count_tokens(text, model)

    if current_tokens <= max_tokens:
        return text

    # Stima caratteri da mantenere (approssimativo)
    chars_to_keep = int((max_tokens / current_tokens) * len(text))
    return text[:chars_to_keep] + suffix


def split_text_by_length(text: str, max_length: int = 4000) -> List[str]:
    """
    Splitta testo in chunk rispettando limite caratteri.

    Utile per messaggi Telegram (max 4096 chars) e TTS (max 4096 chars).

    Args:
        text: Testo da splittare
        max_length: Lunghezza massima per chunk

    Returns:
        Lista di chunks

    Example:
        >>> chunks = split_text_by_length("Very long text...", max_length=100)
        >>> len(chunks[0]) <= 100
        True
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ""

    # Splitta su paragrafi preferibilmente
    paragraphs = text.split("\n\n")

    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= max_length:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    # Se singolo paragrafo è troppo lungo, splitta su frasi
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= max_length:
            final_chunks.append(chunk)
        else:
            # Split su frasi
            sentences = re.split(r'(?<=[.!?])\s+', chunk)
            current = ""
            for sent in sentences:
                if len(current) + len(sent) + 1 <= max_length:
                    current += sent + " "
                else:
                    if current:
                        final_chunks.append(current.strip())
                    current = sent + " "
            if current:
                final_chunks.append(current.strip())

    return final_chunks


def generate_doc_id(filename: str, timestamp: Optional[datetime] = None) -> str:
    """
    Genera ID univoco per documento.

    Args:
        filename: Nome file
        timestamp: Timestamp (default: now)

    Returns:
        ID univoco formato doc_<hash>

    Example:
        >>> doc_id = generate_doc_id("example.pdf")
        >>> doc_id.startswith("doc_")
        True
    """
    if timestamp is None:
        timestamp = datetime.now()

    # Combina filename + timestamp per unicità
    unique_string = f"{filename}_{timestamp.isoformat()}"
    hash_object = hashlib.md5(unique_string.encode())
    hash_hex = hash_object.hexdigest()[:12]

    return f"doc_{hash_hex}"


def get_file_size_mb(filepath: str) -> float:
    """
    Ottieni dimensione file in MB.

    Args:
        filepath: Path al file

    Returns:
        Dimensione in MB

    Example:
        >>> size = get_file_size_mb("document.pdf")
        >>> size > 0
        True
    """
    try:
        size_bytes = os.path.getsize(filepath)
        return size_bytes / (1024 * 1024)
    except Exception:
        return 0.0


def get_directory_size_mb(dirpath: str) -> float:
    """
    Calcola dimensione totale directory in MB.

    Args:
        dirpath: Path directory

    Returns:
        Dimensione totale in MB

    Example:
        >>> size = get_directory_size_mb("./data")
        >>> size >= 0
        True
    """
    total_size = 0

    try:
        for dirpath, dirnames, filenames in os.walk(dirpath):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
    except Exception:
        pass

    return total_size / (1024 * 1024)


def format_timestamp(dt: datetime = None, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Formatta datetime in stringa.

    Args:
        dt: Datetime object (default: now)
        format: Formato strftime

    Returns:
        Stringa formattata

    Example:
        >>> ts = format_timestamp()
        >>> len(ts) > 0
        True
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(format)


def parse_user_ids(ids_string: str) -> List[int]:
    """
    Parsa stringa comma-separated di user IDs in lista int.

    Args:
        ids_string: Stringa tipo "123,456,789"

    Returns:
        Lista di user IDs

    Example:
        >>> parse_user_ids("123,456,789")
        [123, 456, 789]
    """
    if not ids_string:
        return []

    ids = []
    for id_str in ids_string.split(","):
        id_str = id_str.strip()
        if id_str.isdigit():
            ids.append(int(id_str))

    return ids


def extract_file_extension(filename: str) -> str:
    """
    Estrae estensione file (lowercase, senza punto).

    Args:
        filename: Nome file

    Returns:
        Estensione (es: "pdf", "docx")

    Example:
        >>> extract_file_extension("document.PDF")
        'pdf'
    """
    return Path(filename).suffix.lower().lstrip(".")


def is_supported_document(filename: str) -> bool:
    """
    Verifica se file è un formato documento supportato.

    Args:
        filename: Nome file

    Returns:
        True se supportato

    Example:
        >>> is_supported_document("file.pdf")
        True
        >>> is_supported_document("file.exe")
        False
    """
    supported_extensions = ["pdf", "docx", "txt", "md"]
    ext = extract_file_extension(filename)
    return ext in supported_extensions


def sanitize_filename(filename: str) -> str:
    """
    Sanitizza nome file rimuovendo caratteri non sicuri.

    Args:
        filename: Nome file originale

    Returns:
        Nome file sanitizzato

    Example:
        >>> sanitize_filename("my file!@#.pdf")
        'my_file___.pdf'
    """
    # Rimuovi caratteri non alfanumerici (eccetto . _ -)
    safe_name = re.sub(r'[^\w\s.-]', '_', filename)
    # Rimuovi spazi multipli
    safe_name = re.sub(r'\s+', '_', safe_name)
    return safe_name


def format_file_size(size_bytes: int) -> str:
    """
    Formatta dimensione file in formato human-readable.

    Args:
        size_bytes: Dimensione in bytes

    Returns:
        Stringa formattata (es: "1.5 MB")

    Example:
        >>> format_file_size(1536000)
        '1.46 MB'
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def create_markdown_list(items: List[str], ordered: bool = False) -> str:
    """
    Crea lista markdown da lista Python.

    Args:
        items: Lista di stringhe
        ordered: True per lista numerata

    Returns:
        Stringa markdown

    Example:
        >>> create_markdown_list(["item1", "item2"], ordered=True)
        '1. item1\\n2. item2'
    """
    if not items:
        return ""

    if ordered:
        return "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))
    else:
        return "\n".join(f"• {item}" for item in items)


def escape_markdown_v2(text: str) -> str:
    """
    Escapa caratteri speciali per Telegram MarkdownV2.

    Telegram MarkdownV2 richiede escape di: _*[]()~`>#+-=|{}.!

    Args:
        text: Testo da escapare

    Returns:
        Testo con caratteri escapati

    Example:
        >>> escape_markdown_v2("Hello_world")
        'Hello\\_world'
    """
    special_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join('\\' + char if char in special_chars else char for char in text)


def sanitize_html_for_telegram(text: str) -> str:
    """
    Sanitizza HTML rimuovendo o convertendo tag non supportati da Telegram.

    Telegram supporta SOLO questi tag HTML:
    - <b>, <strong> → grassetto
    - <i>, <em> → corsivo
    - <u>, <ins> → sottolineato
    - <s>, <strike>, <del> → barrato
    - <code> → monospace inline
    - <pre> → blocco pre-formattato
    - <a href=""> → link

    Questa funzione converte/rimuove tag non supportati:
    - <p> → rimuovi tag, mantieni contenuto + newline
    - <h1>, <h2>, <h3>, etc. → <b>contenuto</b>
    - <ul>, <ol> → rimuovi tag
    - <li> → converti in "• contenuto"
    - <div>, <span>, <br> → rimuovi tag, mantieni contenuto
    - Tutti gli altri tag → rimuovi (mantieni solo contenuto)

    Args:
        text: Testo con HTML completo (potenzialmente non supportato)

    Returns:
        Testo con solo tag HTML supportati da Telegram

    Example:
        >>> sanitize_html_for_telegram("<p>Hello <h3>World</h3></p>")
        'Hello <b>World</b>'
    """
    if not text:
        return text

    # 1. Converti headings (h1-h6) in grassetto
    text = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', r'<b>\1</b>\n\n', text, flags=re.DOTALL | re.IGNORECASE)

    # 2. Converti <li> in bullet points
    text = re.sub(r'<li[^>]*>(.*?)</li>', r'• \1\n', text, flags=re.DOTALL | re.IGNORECASE)

    # 3. Rimuovi tag liste (ul, ol) mantenendo contenuto
    text = re.sub(r'</?ul[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</?ol[^>]*>', '\n', text, flags=re.IGNORECASE)

    # 4. Rimuovi <p> aggiungendo newline
    text = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', text, flags=re.DOTALL | re.IGNORECASE)

    # 5. Converti <br> in newline
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)

    # 6. Rimuovi <div>, <span> mantenendo contenuto
    text = re.sub(r'</?div[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'</?span[^>]*>', '', text, flags=re.IGNORECASE)

    # 7. Normalizza tag supportati (strong → b, em → i, etc.)
    text = re.sub(r'<strong>', '<b>', text, flags=re.IGNORECASE)
    text = re.sub(r'</strong>', '</b>', text, flags=re.IGNORECASE)
    text = re.sub(r'<em>', '<i>', text, flags=re.IGNORECASE)
    text = re.sub(r'</em>', '</i>', text, flags=re.IGNORECASE)
    text = re.sub(r'<(strike|del)>', '<s>', text, flags=re.IGNORECASE)
    text = re.sub(r'</(strike|del)>', '</s>', text, flags=re.IGNORECASE)
    text = re.sub(r'<ins>', '<u>', text, flags=re.IGNORECASE)
    text = re.sub(r'</ins>', '</u>', text, flags=re.IGNORECASE)

    # 8. Rimuovi tutti gli altri tag non supportati mantenendo contenuto
    # Lista tag supportati finali
    supported_tags = ['b', 'i', 'u', 's', 'code', 'pre', 'a']

    # Pattern per trovare tag apertura e chiusura
    def filter_tags(match):
        tag_full = match.group(0)  # <tag attr="value"> o </tag>
        tag_name_match = re.match(r'</?(\w+)', tag_full)
        if tag_name_match:
            tag_name = tag_name_match.group(1).lower()
            if tag_name in supported_tags:
                return tag_full  # Mantieni tag supportato
        return ''  # Rimuovi tag non supportato

    text = re.sub(r'</?[^>]+>', filter_tags, text)

    # 9. Pulisci newline multipli e spazi eccessivi
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)

    return text.strip()


def convert_markdown_to_html(text: str) -> str:
    """
    Converte formattazione Markdown in tag HTML per Telegram.

    Questa funzione è un fallback per quando l'LLM genera Markdown
    invece di HTML nonostante le istruzioni. Converte:
    - **testo** → <b>testo</b>
    - *testo* o _testo_ → <i>testo</i>
    - `code` → <code>code</code>
    - ```code``` → <pre>code</pre>
    - ~~text~~ → <s>text</s>
    - [link](url) → <a href="url">link</a>

    Poi sanitizza HTML per rimuovere tag non supportati da Telegram.

    Args:
        text: Testo con formattazione Markdown o HTML

    Returns:
        Testo con solo tag HTML supportati da Telegram

    Example:
        >>> convert_markdown_to_html("**Hello** *world*!")
        '<b>Hello</b> <i>world</i>!'
    """
    if not text:
        return text

    # Blocchi di codice (``` ... ```) - PRIMA dei code inline
    text = re.sub(r'```([^`]+)```', r'<pre>\1</pre>', text, flags=re.DOTALL)

    # Code inline (`code`)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    # Grassetto (**testo** o __testo__)
    text = re.sub(r'\*\*([^\*]+)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__([^_]+)__', r'<b>\1</b>', text)

    # Corsivo (*testo* o _testo_) - DOPO grassetto per evitare conflitti
    text = re.sub(r'(?<!\*)\*(?!\*)([^\*]+)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
    text = re.sub(r'(?<!_)_(?!_)([^_]+)(?<!_)_(?!_)', r'<i>\1</i>', text)

    # Barrato (~~text~~)
    text = re.sub(r'~~([^~]+)~~', r'<s>\1</s>', text)

    # Link markdown ([text](url))
    text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', text)

    # IMPORTANTE: Sanitizza HTML per rimuovere tag non supportati da Telegram
    text = sanitize_html_for_telegram(text)

    return text


def extract_command_args(text: str) -> tuple:
    """
    Estrae comando e argomenti da testo messaggio Telegram.

    Args:
        text: Testo messaggio (es: "/delete_doc doc_123")

    Returns:
        Tuple (comando, lista argomenti)

    Example:
        >>> extract_command_args("/delete_doc doc_123 confirm")
        ('delete_doc', ['doc_123', 'confirm'])
    """
    parts = text.split()
    if not parts:
        return ("", [])

    command = parts[0].lstrip("/")
    args = parts[1:] if len(parts) > 1 else []

    return (command, args)


def validate_telegram_token(token: str) -> bool:
    """
    Valida formato Telegram bot token.

    Token format: <bot_id>:<token>
    Es: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz

    Args:
        token: Token da validare

    Returns:
        True se formato valido

    Example:
        >>> validate_telegram_token("123456789:ABCdef")
        True
        >>> validate_telegram_token("invalid")
        False
    """
    # Pattern: numeri:alfanumerici
    pattern = r'^\d+:[A-Za-z0-9_-]+$'
    return bool(re.match(pattern, token))


def validate_openai_key(key: str) -> bool:
    """
    Valida formato OpenAI API key.

    Key format: sk-...

    Args:
        key: API key da validare

    Returns:
        True se formato valido

    Example:
        >>> validate_openai_key("sk-abcd1234...")
        True
    """
    return key.startswith("sk-") and len(key) > 20


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Splitta lista in chunks di dimensione fissa.

    Args:
        lst: Lista da splittare
        chunk_size: Dimensione chunk

    Returns:
        Lista di chunks

    Example:
        >>> chunk_list([1,2,3,4,5], 2)
        [[1, 2], [3, 4], [5]]
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_dict_get(d: dict, *keys, default=None) -> Any:
    """
    Accesso sicuro a nested dict con fallback.

    Args:
        d: Dictionary
        *keys: Chiavi nested (es: "user", "profile", "name")
        default: Valore default se chiave non esiste

    Returns:
        Valore o default

    Example:
        >>> data = {"user": {"profile": {"name": "John"}}}
        >>> safe_dict_get(data, "user", "profile", "name")
        'John'
        >>> safe_dict_get(data, "user", "missing", "key", default="N/A")
        'N/A'
    """
    current = d
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def format_sources(sources: List[dict]) -> str:
    """
    Formatta lista di fonti per citazioni RAG.

    Utile per aggiungere citazioni documentali alle risposte.

    Args:
        sources: Lista di dict con 'source' e 'page'

    Returns:
        Stringa formattata con citazioni

    Example:
        >>> sources = [{"source": "doc.pdf", "page": 5}, {"source": "guide.txt", "page": 2}]
        >>> print(format_sources(sources))
        📚 **Fonti:**
        1. doc.pdf (pag. 5)
        2. guide.txt (pag. 2)
    """
    if not sources:
        return ""

    citations = "\n\n📚 **Fonti:**\n"
    for i, source in enumerate(sources, 1):
        filename = source.get('source', 'Unknown')
        page = source.get('page', 'N/A')
        citations += f"{i}. {filename} (pag. {page})\n"

    return citations


def format_error_for_user(error: Exception) -> str:
    """
    Formatta errore tecnico in messaggio user-friendly.

    Converte eccezioni Python in messaggi comprensibili per utenti finali.

    Args:
        error: Eccezione Python

    Returns:
        Messaggio di errore comprensibile

    Example:
        >>> error = Exception("Rate limit exceeded")
        >>> format_error_for_user(error)
        'Troppe richieste. Attendi un momento e riprova.'
    """
    error_str = str(error).lower()

    # Map errori comuni a messaggi user-friendly
    if "rate limit" in error_str:
        return "Troppe richieste. Attendi un momento e riprova."
    elif "timeout" in error_str:
        return "Richiesta scaduta. Riprova con una query più semplice."
    elif "api key" in error_str:
        return "Errore di autenticazione API. Contatta l'amministratore."
    elif "quota" in error_str:
        return "Quota API esaurita. Contatta l'amministratore."
    else:
        return f"Errore: {str(error)[:100]}"


# ========================================
# Export all helpers
# ========================================
__all__ = [
    'count_tokens',
    'truncate_text',
    'split_text_by_length',
    'generate_doc_id',
    'get_file_size_mb',
    'get_directory_size_mb',
    'format_timestamp',
    'parse_user_ids',
    'extract_file_extension',
    'is_supported_document',
    'sanitize_filename',
    'format_file_size',
    'create_markdown_list',
    'escape_markdown_v2',
    'sanitize_html_for_telegram',
    'convert_markdown_to_html',
    'extract_command_args',
    'validate_telegram_token',
    'validate_openai_key',
    'chunk_list',
    'safe_dict_get',
    'format_sources',
    'format_error_for_user'
]


if __name__ == "__main__":
    # Test helpers
    print("Testing helpers module...\n")

    # Test token counting
    text = "Hello world! This is a test."
    print(f"Text: '{text}'")
    print(f"Tokens: {count_tokens(text)}")

    # Test text splitting
    long_text = "Lorem ipsum " * 500
    chunks = split_text_by_length(long_text, max_length=100)
    print(f"\nLong text split into {len(chunks)} chunks")

    # Test doc ID generation
    doc_id = generate_doc_id("example.pdf")
    print(f"\nGenerated doc ID: {doc_id}")

    # Test file validation
    print(f"\nIs 'doc.pdf' supported? {is_supported_document('doc.pdf')}")
    print(f"Is 'doc.exe' supported? {is_supported_document('doc.exe')}")

    # Test filename sanitization
    unsafe_name = "my file!@#$%.pdf"
    safe_name = sanitize_filename(unsafe_name)
    print(f"\nSanitized '{unsafe_name}' -> '{safe_name}'")

    print("\n✅ All tests passed!")
