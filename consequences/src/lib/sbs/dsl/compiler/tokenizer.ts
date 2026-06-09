import { Token, TokenType } from './types';

export const KEYWORDS = new Set([
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

const TWO_CHAR_OPS = new Set([
  '==', '!=', '<=', '>=', '&&', '||', '**', '+=', '-=', '*=', '/=',
]);

const SINGLE_CHAR_OPS = new Set(['+', '-', '*', '/', '%', '<', '>', '=', '!']);
const PUNCTUATION = new Set(['(', ')', '{', '}', '[', ']', ',', ':', ';', '.', '@', '#']);

export function tokenize(source: string): Token[] {
  const tokens: Token[] = [];
  let i = 0;
  let line = 1;
  let col = 1;

  while (i < source.length) {
    const ch = source[i];

    if (ch === '\n') {
      line++;
      col = 1;
      i++;
      continue;
    }

    if (/\s/.test(ch)) {
      col++;
      i++;
      continue;
    }

    // Single-line comment
    if (ch === '/' && source[i + 1] === '/') {
      while (i < source.length && source[i] !== '\n') i++;
      continue;
    }

    // Multi-line comment
    if (ch === '/' && source[i + 1] === '*') {
      const startLine = line;
      const startCol = col;
      i += 2;
      col += 2;
      while (i < source.length - 1 && !(source[i] === '*' && source[i + 1] === '/')) {
        if (source[i] === '\n') {
          line++;
          col = 1;
        } else {
          col++;
        }
        i++;
      }
      if (i >= source.length - 1) {
        throw new SBSTokenError(`Unterminated block comment`, startLine, startCol);
      }
      i += 2;
      col += 2;
      continue;
    }

    // Arrow ->
    if (ch === '-' && source[i + 1] === '>') {
      tokens.push({ type: TokenType.ARROW, value: '->', line, col });
      i += 2;
      col += 2;
      continue;
    }

    // Pipe |>
    if (ch === '|' && source[i + 1] === '>') {
      tokens.push({ type: TokenType.PIPE, value: '|>', line, col });
      i += 2;
      col += 2;
      continue;
    }

    // Back-arrow <-
    if (ch === '<' && source[i + 1] === '-') {
      tokens.push({ type: TokenType.ARROW, value: '<-', line, col });
      i += 2;
      col += 2;
      continue;
    }

    // Two-char operators
    const twoChar = source.slice(i, i + 2);
    if (TWO_CHAR_OPS.has(twoChar)) {
      tokens.push({ type: TokenType.OP, value: twoChar, line, col });
      i += 2;
      col += 2;
      continue;
    }

    // Single-char operators
    if (SINGLE_CHAR_OPS.has(ch)) {
      tokens.push({ type: TokenType.OP, value: ch, line, col });
      i++;
      col++;
      continue;
    }

    // Punctuation
    if (PUNCTUATION.has(ch)) {
      tokens.push({ type: TokenType.PUNC, value: ch, line, col });
      i++;
      col++;
      continue;
    }

    // String literals
    if (ch === '"' || ch === "'") {
      const startLine = line;
      const startCol = col;
      const quote = ch;
      let str = '';
      i++;
      col++;
      while (i < source.length && source[i] !== quote) {
        if (source[i] === '\\' && i + 1 < source.length) {
          const esc = source[i + 1];
          switch (esc) {
            case 'n': str += '\n'; break;
            case 't': str += '\t'; break;
            case '\\': str += '\\'; break;
            case '"': str += '"'; break;
            case "'": str += "'"; break;
            default: str += esc;
          }
          i += 2;
          col += 2;
          continue;
        }
        if (source[i] === '\n') {
          throw new SBSTokenError(`Unterminated string literal`, startLine, startCol);
        }
        str += source[i];
        i++;
        col++;
      }
      if (i >= source.length) {
        throw new SBSTokenError(`Unterminated string literal`, startLine, startCol);
      }
      i++; // skip closing quote
      col++;
      tokens.push({ type: TokenType.STRING, value: str, line: startLine, col: startCol });
      continue;
    }

    // Number literals
    if (/[0-9]/.test(ch) || (ch === '.' && i + 1 < source.length && /[0-9]/.test(source[i + 1]))) {
      const startCol = col;
      let num = '';
      let hasDecimal = false;
      let hasExponent = false;

      while (i < source.length) {
        const c = source[i];
        if (/[0-9]/.test(c)) {
          num += c;
        } else if (c === '.' && !hasDecimal && !hasExponent) {
          hasDecimal = true;
          num += c;
        } else if ((c === 'e' || c === 'E') && !hasExponent) {
          hasExponent = true;
          num += c;
          if (i + 1 < source.length && (source[i + 1] === '+' || source[i + 1] === '-')) {
            num += source[i + 1];
            i++;
            col++;
          }
        } else {
          break;
        }
        i++;
        col++;
      }

      const parsed = parseFloat(num);
      if (isNaN(parsed)) {
        throw new SBSTokenError(`Invalid number literal '${num}'`, line, startCol);
      }
      tokens.push({ type: TokenType.NUMBER, value: parsed, line, col: startCol });
      continue;
    }

    // Identifiers and keywords
    if (/[a-zA-Z_]/.test(ch)) {
      const startCol = col;
      let id = '';
      while (i < source.length && /[a-zA-Z0-9_]/.test(source[i])) {
        id += source[i];
        i++;
        col++;
      }
      const type = KEYWORDS.has(id) ? TokenType.KEYWORD : TokenType.IDENT;
      tokens.push({ type, value: id, line, col: startCol });
      continue;
    }

    throw new SBSTokenError(`Unexpected character '${ch}'`, line, col);
  }

  tokens.push({ type: TokenType.EOF, value: null, line, col });
  return tokens;
}

export class SBSTokenError extends Error {
  line: number;
  col: number;

  constructor(message: string, line: number, col: number) {
    super(`${message} at line ${line}, col ${col}`);
    this.name = 'SBSTokenError';
    this.line = line;
    this.col = col;
  }
}
