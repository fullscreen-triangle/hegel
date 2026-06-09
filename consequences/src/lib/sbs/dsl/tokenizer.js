const TOKEN_TYPES = {
  KEYWORD: 'KEYWORD',
  IDENT: 'IDENT',
  NUMBER: 'NUMBER',
  STRING: 'STRING',
  OP: 'OP',
  PUNC: 'PUNC',
  ARROW: 'ARROW',
  PIPE: 'PIPE',
  EOF: 'EOF',
};

const KEYWORDS = new Set([
  'circuit', 'node', 'edge', 'let', 'fn', 'return',
  'observe', 'perturb', 'restore', 'navigate',
  'Se', 'Sk', 'St', 'R', 'V',
  'triple', 'catalyst', 'compose', 'cascade',
  'floor', 'coherence', 'visibility',
  'for', 'in', 'if', 'else', 'true', 'false',
  'import', 'export', 'as',
  'osc', 'cat', 'part',
  'convert', 'from', 'to',
]);

function tokenize(source) {
  const tokens = [];
  let i = 0;
  let line = 1;
  let col = 1;

  while (i < source.length) {
    const ch = source[i];

    if (ch === '\n') { line++; col = 1; i++; continue; }
    if (/\s/.test(ch)) { col++; i++; continue; }

    if (ch === '/' && source[i + 1] === '/') {
      while (i < source.length && source[i] !== '\n') i++;
      continue;
    }

    if (ch === '/' && source[i + 1] === '*') {
      i += 2; col += 2;
      while (i < source.length - 1 && !(source[i] === '*' && source[i + 1] === '/')) {
        if (source[i] === '\n') { line++; col = 1; } else col++;
        i++;
      }
      i += 2; col += 2;
      continue;
    }

    if (ch === '-' && source[i + 1] === '>') {
      tokens.push({ type: TOKEN_TYPES.ARROW, value: '->', line, col });
      i += 2; col += 2; continue;
    }

    if (ch === '|' && source[i + 1] === '>') {
      tokens.push({ type: TOKEN_TYPES.PIPE, value: '|>', line, col });
      i += 2; col += 2; continue;
    }

    if (ch === '<' && source[i + 1] === '-') {
      tokens.push({ type: TOKEN_TYPES.ARROW, value: '<-', line, col });
      i += 2; col += 2; continue;
    }

    const twoChar = source.slice(i, i + 2);
    if (['==', '!=', '<=', '>=', '&&', '||', '**', '+=', '-=', '*=', '/='].includes(twoChar)) {
      tokens.push({ type: TOKEN_TYPES.OP, value: twoChar, line, col });
      i += 2; col += 2; continue;
    }

    if ('+-*/%<>=!'.includes(ch)) {
      tokens.push({ type: TOKEN_TYPES.OP, value: ch, line, col });
      i++; col++; continue;
    }

    if ('(){}[],:;.@#'.includes(ch)) {
      tokens.push({ type: TOKEN_TYPES.PUNC, value: ch, line, col });
      i++; col++; continue;
    }

    if (ch === '"' || ch === "'") {
      const quote = ch;
      let str = '';
      i++; col++;
      while (i < source.length && source[i] !== quote) {
        if (source[i] === '\\') { i++; col++; }
        str += source[i];
        i++; col++;
      }
      i++; col++;
      tokens.push({ type: TOKEN_TYPES.STRING, value: str, line, col });
      continue;
    }

    if (/[0-9]/.test(ch) || (ch === '.' && /[0-9]/.test(source[i + 1]))) {
      let num = '';
      while (i < source.length && /[0-9.eE\-+]/.test(source[i])) {
        if ((source[i] === '-' || source[i] === '+') && !/[eE]/.test(source[i - 1])) break;
        num += source[i]; i++; col++;
      }
      tokens.push({ type: TOKEN_TYPES.NUMBER, value: parseFloat(num), line, col });
      continue;
    }

    if (/[a-zA-Z_]/.test(ch)) {
      let id = '';
      while (i < source.length && /[a-zA-Z0-9_]/.test(source[i])) {
        id += source[i]; i++; col++;
      }
      const type = KEYWORDS.has(id) ? TOKEN_TYPES.KEYWORD : TOKEN_TYPES.IDENT;
      tokens.push({ type, value: id, line, col });
      continue;
    }

    throw new Error(`Unexpected character '${ch}' at line ${line}, col ${col}`);
  }

  tokens.push({ type: TOKEN_TYPES.EOF, value: null, line, col });
  return tokens;
}

export { tokenize, TOKEN_TYPES, KEYWORDS };
