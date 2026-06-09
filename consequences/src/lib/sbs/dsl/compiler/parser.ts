import {
  Token, TokenType,
  ASTNode, Expression, Program,
  CircuitDecl, NodeDecl, EdgeDecl, LetDecl, FnDecl,
  ObserveStmt, PerturbStmt, RestoreStmt, NavigateStmt,
  CatalystDecl, CascadeStmt, ConvertStmt,
  ForLoop, IfStatement, ImportStmt, ExportStmt,
  ExpressionStatement,
} from './types';

export class SBSParseError extends Error {
  line: number;
  col: number;

  constructor(message: string, line: number, col: number) {
    super(`${message} at line ${line}, col ${col}`);
    this.name = 'SBSParseError';
    this.line = line;
    this.col = col;
  }
}

const RECOVERY_KEYWORDS = new Set([
  'circuit', 'node', 'edge', 'let', 'fn',
  'observe', 'perturb', 'restore', 'navigate',
  'catalyst', 'cascade', 'convert',
  'for', 'if', 'import', 'export',
]);

export class Parser {
  private tokens: Token[];
  private pos: number;
  private errors: SBSParseError[];

  constructor(tokens: Token[]) {
    this.tokens = tokens;
    this.pos = 0;
    this.errors = [];
  }

  private peek(): Token {
    return this.tokens[this.pos];
  }

  private advance(): Token {
    return this.tokens[this.pos++];
  }

  private expect(type: TokenType, value?: string): Token {
    const tok = this.advance();
    if (tok.type !== type || (value !== undefined && tok.value !== value)) {
      const expected = value ? `${type} '${value}'` : type;
      throw new SBSParseError(
        `Expected ${expected} but got ${tok.type} '${tok.value}'`,
        tok.line, tok.col,
      );
    }
    return tok;
  }

  private match(type: TokenType, value?: string): Token | null {
    const tok = this.peek();
    if (tok.type === type && (value === undefined || tok.value === value)) {
      return this.advance();
    }
    return null;
  }

  private recover(): void {
    while (this.peek().type !== TokenType.EOF) {
      if (this.peek().type === TokenType.KEYWORD && RECOVERY_KEYWORDS.has(this.peek().value as string)) {
        return;
      }
      if (this.peek().type === TokenType.PUNC && this.peek().value === '}') {
        this.advance();
        return;
      }
      this.advance();
    }
  }

  parse(): { ast: Program; errors: SBSParseError[] } {
    const program: Program = { type: 'Program', body: [] };

    while (this.peek().type !== TokenType.EOF) {
      try {
        program.body.push(this.parseStatement());
      } catch (err) {
        if (err instanceof SBSParseError) {
          this.errors.push(err);
          this.recover();
        } else {
          throw err;
        }
      }
    }

    return { ast: program, errors: this.errors };
  }

  private parseStatement(): ASTNode {
    const tok = this.peek();

    if (tok.type === TokenType.KEYWORD) {
      switch (tok.value) {
        case 'circuit': return this.parseCircuitDecl();
        case 'node': return this.parseNodeDecl();
        case 'edge': return this.parseEdgeDecl();
        case 'let': return this.parseLetDecl();
        case 'fn': return this.parseFnDecl();
        case 'observe': return this.parseObserve();
        case 'perturb': return this.parsePerturb();
        case 'restore': return this.parseRestore();
        case 'navigate': return this.parseNavigate();
        case 'catalyst': return this.parseCatalyst();
        case 'cascade': return this.parseCascade();
        case 'convert': return this.parseConvert();
        case 'for': return this.parseFor();
        case 'if': return this.parseIf();
        case 'import': return this.parseImport();
        case 'export': return this.parseExport();
      }
    }

    const expr = this.parseExpression();
    this.match(TokenType.PUNC, ';');
    return { type: 'ExpressionStatement', expression: expr } as ExpressionStatement;
  }

  private parseCircuitDecl(): CircuitDecl {
    this.expect(TokenType.KEYWORD, 'circuit');
    const name = this.expect(TokenType.IDENT).value as string;
    this.expect(TokenType.PUNC, '{');
    const body: ASTNode[] = [];
    while (!this.match(TokenType.PUNC, '}')) {
      if (this.peek().type === TokenType.EOF) {
        throw new SBSParseError('Unterminated circuit block', this.peek().line, this.peek().col);
      }
      body.push(this.parseStatement());
    }
    return { type: 'CircuitDecl', name, body };
  }

  private parseNodeDecl(): NodeDecl {
    this.expect(TokenType.KEYWORD, 'node');
    const name = this.expect(TokenType.IDENT).value as string;
    const props = this.parseProps();
    this.match(TokenType.PUNC, ';');
    return { type: 'NodeDecl', name, props };
  }

  private parseEdgeDecl(): EdgeDecl {
    this.expect(TokenType.KEYWORD, 'edge');
    const src = this.expect(TokenType.IDENT).value as string;
    this.expect(TokenType.ARROW, '->');
    const dst = this.expect(TokenType.IDENT).value as string;
    const props = this.parseProps();
    this.match(TokenType.PUNC, ';');
    return { type: 'EdgeDecl', src, dst, props };
  }

  private parseLetDecl(): LetDecl {
    this.expect(TokenType.KEYWORD, 'let');
    const name = this.expect(TokenType.IDENT).value as string;
    this.expect(TokenType.OP, '=');
    const init = this.parseExpression();
    this.match(TokenType.PUNC, ';');
    return { type: 'LetDecl', name, init };
  }

  private parseFnDecl(): FnDecl {
    this.expect(TokenType.KEYWORD, 'fn');
    const name = this.expect(TokenType.IDENT).value as string;
    this.expect(TokenType.PUNC, '(');
    const params: string[] = [];
    while (!this.match(TokenType.PUNC, ')')) {
      if (params.length > 0) this.expect(TokenType.PUNC, ',');
      params.push(this.expect(TokenType.IDENT).value as string);
    }
    this.expect(TokenType.PUNC, '{');
    const body: ASTNode[] = [];
    while (!this.match(TokenType.PUNC, '}')) {
      if (this.peek().type === TokenType.EOF) {
        throw new SBSParseError('Unterminated function block', this.peek().line, this.peek().col);
      }
      body.push(this.parseStatement());
    }
    return { type: 'FnDecl', name, params, body };
  }

  private parseObserve(): ObserveStmt {
    this.expect(TokenType.KEYWORD, 'observe');
    const target = this.parseExpression();
    this.match(TokenType.PUNC, ';');
    return { type: 'Observe', target };
  }

  private parsePerturb(): PerturbStmt {
    this.expect(TokenType.KEYWORD, 'perturb');
    const target = this.parseExpression();
    const props = this.parseProps();
    this.match(TokenType.PUNC, ';');
    return { type: 'Perturb', target, props };
  }

  private parseRestore(): RestoreStmt {
    this.expect(TokenType.KEYWORD, 'restore');
    const target = this.parseExpression();
    this.match(TokenType.PUNC, ';');
    return { type: 'Restore', target };
  }

  private parseNavigate(): NavigateStmt {
    this.expect(TokenType.KEYWORD, 'navigate');
    const direction = this.match(TokenType.KEYWORD, 'from') ? 'backward' as const : 'forward' as const;
    const target = this.parseExpression();
    this.match(TokenType.PUNC, ';');
    return { type: 'Navigate', direction, target };
  }

  private parseCatalyst(): CatalystDecl {
    this.expect(TokenType.KEYWORD, 'catalyst');
    const name = this.expect(TokenType.IDENT).value as string;
    const props = this.parseProps();
    this.match(TokenType.PUNC, ';');
    return { type: 'CatalystDecl', name, props };
  }

  private parseCascade(): CascadeStmt {
    this.expect(TokenType.KEYWORD, 'cascade');
    this.expect(TokenType.PUNC, '(');
    const catalysts: Expression[] = [];
    while (!this.match(TokenType.PUNC, ')')) {
      if (catalysts.length > 0) this.expect(TokenType.PUNC, ',');
      catalysts.push(this.parseExpression());
    }
    this.match(TokenType.PUNC, ';');
    return { type: 'Cascade', catalysts };
  }

  private parseConvert(): ConvertStmt {
    this.expect(TokenType.KEYWORD, 'convert');
    const expr = this.parseExpression();
    this.expect(TokenType.KEYWORD, 'from');
    const from = this.expect(TokenType.KEYWORD).value as string;
    this.expect(TokenType.KEYWORD, 'to');
    const to = this.expect(TokenType.KEYWORD).value as string;
    this.match(TokenType.PUNC, ';');
    return { type: 'Convert', expr, from, to };
  }

  private parseFor(): ForLoop {
    this.expect(TokenType.KEYWORD, 'for');
    const variable = this.expect(TokenType.IDENT).value as string;
    this.expect(TokenType.KEYWORD, 'in');
    const iterable = this.parseExpression();
    this.expect(TokenType.PUNC, '{');
    const body: ASTNode[] = [];
    while (!this.match(TokenType.PUNC, '}')) {
      if (this.peek().type === TokenType.EOF) {
        throw new SBSParseError('Unterminated for block', this.peek().line, this.peek().col);
      }
      body.push(this.parseStatement());
    }
    return { type: 'ForLoop', variable, iterable, body };
  }

  private parseIf(): IfStatement {
    this.expect(TokenType.KEYWORD, 'if');
    const condition = this.parseExpression();
    this.expect(TokenType.PUNC, '{');
    const consequent: ASTNode[] = [];
    while (!this.match(TokenType.PUNC, '}')) {
      if (this.peek().type === TokenType.EOF) {
        throw new SBSParseError('Unterminated if block', this.peek().line, this.peek().col);
      }
      consequent.push(this.parseStatement());
    }
    let alternate: ASTNode[] | null = null;
    if (this.match(TokenType.KEYWORD, 'else')) {
      if (this.peek().value === 'if') {
        alternate = [this.parseIf()];
      } else {
        this.expect(TokenType.PUNC, '{');
        alternate = [];
        while (!this.match(TokenType.PUNC, '}')) {
          if (this.peek().type === TokenType.EOF) {
            throw new SBSParseError('Unterminated else block', this.peek().line, this.peek().col);
          }
          alternate.push(this.parseStatement());
        }
      }
    }
    return { type: 'IfStatement', condition, consequent, alternate };
  }

  private parseImport(): ImportStmt {
    this.expect(TokenType.KEYWORD, 'import');
    const name = this.expect(TokenType.IDENT).value as string;
    let alias: string | null = null;
    if (this.match(TokenType.KEYWORD, 'as')) {
      alias = this.expect(TokenType.IDENT).value as string;
    }
    this.expect(TokenType.KEYWORD, 'from');
    const source = this.expect(TokenType.STRING).value as string;
    this.match(TokenType.PUNC, ';');
    return { type: 'Import', name, alias, source };
  }

  private parseExport(): ExportStmt {
    this.expect(TokenType.KEYWORD, 'export');
    const declaration = this.parseStatement();
    return { type: 'Export', declaration };
  }

  private parseProps(): Record<string, Expression> {
    if (!this.match(TokenType.PUNC, '{')) return {};
    const props: Record<string, Expression> = {};
    while (!this.match(TokenType.PUNC, '}')) {
      if (this.peek().type === TokenType.EOF) {
        throw new SBSParseError('Unterminated property block', this.peek().line, this.peek().col);
      }
      const key = this.expect(TokenType.IDENT).value as string;
      this.expect(TokenType.PUNC, ':');
      props[key] = this.parseExpression();
      this.match(TokenType.PUNC, ',');
    }
    return props;
  }

  // ── Expression parsing (precedence climbing) ──

  private parseExpression(): Expression {
    return this.parsePipe();
  }

  private parsePipe(): Expression {
    let left = this.parseOr();
    while (this.match(TokenType.PIPE)) {
      const right = this.parseOr();
      left = { type: 'PipeExpr', left, right };
    }
    return left;
  }

  private parseOr(): Expression {
    let left = this.parseAnd();
    while (this.match(TokenType.OP, '||')) {
      left = { type: 'BinaryExpr', op: '||', left, right: this.parseAnd() };
    }
    return left;
  }

  private parseAnd(): Expression {
    let left = this.parseComparison();
    while (this.match(TokenType.OP, '&&')) {
      left = { type: 'BinaryExpr', op: '&&', left, right: this.parseComparison() };
    }
    return left;
  }

  private parseComparison(): Expression {
    let left = this.parseAddSub();
    const compOps = new Set(['==', '!=', '<', '>', '<=', '>=']);
    while (this.peek().type === TokenType.OP && compOps.has(this.peek().value as string)) {
      const op = this.advance().value as string;
      left = { type: 'BinaryExpr', op, left, right: this.parseAddSub() };
    }
    return left;
  }

  private parseAddSub(): Expression {
    let left = this.parseMulDiv();
    while (this.peek().type === TokenType.OP && (this.peek().value === '+' || this.peek().value === '-')) {
      const op = this.advance().value as string;
      left = { type: 'BinaryExpr', op, left, right: this.parseMulDiv() };
    }
    return left;
  }

  private parseMulDiv(): Expression {
    let left = this.parsePower();
    while (this.peek().type === TokenType.OP && (this.peek().value === '*' || this.peek().value === '/' || this.peek().value === '%')) {
      const op = this.advance().value as string;
      left = { type: 'BinaryExpr', op, left, right: this.parsePower() };
    }
    return left;
  }

  private parsePower(): Expression {
    let left = this.parseUnary();
    if (this.match(TokenType.OP, '**')) {
      // right-associative
      left = { type: 'BinaryExpr', op: '**', left, right: this.parsePower() };
    }
    return left;
  }

  private parseUnary(): Expression {
    if (this.peek().type === TokenType.OP && (this.peek().value === '-' || this.peek().value === '!')) {
      const op = this.advance().value as string;
      return { type: 'UnaryExpr', op, operand: this.parseUnary() };
    }
    return this.parsePostfix();
  }

  private parsePostfix(): Expression {
    let expr = this.parsePrimary();
    while (true) {
      if (this.match(TokenType.PUNC, '.')) {
        const prop = this.expect(TokenType.IDENT).value as string;
        if (this.match(TokenType.PUNC, '(')) {
          const args = this.parseArgList();
          expr = { type: 'MethodCall', object: expr, method: prop, args };
        } else {
          expr = { type: 'MemberExpr', object: expr, property: prop };
        }
      } else if (this.match(TokenType.PUNC, '(')) {
        const args = this.parseArgList();
        expr = { type: 'CallExpr', callee: expr, args };
      } else if (this.match(TokenType.PUNC, '[')) {
        const index = this.parseExpression();
        this.expect(TokenType.PUNC, ']');
        expr = { type: 'IndexExpr', object: expr, index };
      } else {
        break;
      }
    }
    return expr;
  }

  private parseArgList(): Expression[] {
    const args: Expression[] = [];
    while (!this.match(TokenType.PUNC, ')')) {
      if (args.length > 0) this.expect(TokenType.PUNC, ',');
      args.push(this.parseExpression());
    }
    return args;
  }

  private parsePrimary(): Expression {
    const tok = this.peek();

    if (tok.type === TokenType.NUMBER) {
      this.advance();
      return { type: 'NumberLiteral', value: tok.value as number };
    }

    if (tok.type === TokenType.STRING) {
      this.advance();
      return { type: 'StringLiteral', value: tok.value as string };
    }

    if (tok.type === TokenType.KEYWORD && (tok.value === 'true' || tok.value === 'false')) {
      this.advance();
      return { type: 'BooleanLiteral', value: tok.value === 'true' };
    }

    const builtins = new Set(['Se', 'Sk', 'St', 'R', 'V', 'floor', 'coherence', 'visibility']);
    if (tok.type === TokenType.KEYWORD && builtins.has(tok.value as string)) {
      this.advance();
      return { type: 'BuiltinRef', name: tok.value as string };
    }

    if (tok.type === TokenType.KEYWORD && tok.value === 'triple') {
      this.advance();
      this.expect(TokenType.PUNC, '(');
      const k = this.parseExpression();
      this.expect(TokenType.PUNC, ',');
      const t = this.parseExpression();
      this.expect(TokenType.PUNC, ',');
      const e = this.parseExpression();
      this.expect(TokenType.PUNC, ')');
      return { type: 'TripleExpr', k, t, e };
    }

    if (tok.type === TokenType.IDENT) {
      this.advance();
      return { type: 'Identifier', name: tok.value as string };
    }

    if (tok.type === TokenType.PUNC && tok.value === '(') {
      this.advance();
      const expr = this.parseExpression();
      this.expect(TokenType.PUNC, ')');
      return expr;
    }

    if (tok.type === TokenType.PUNC && tok.value === '[') {
      this.advance();
      const elements: Expression[] = [];
      while (!this.match(TokenType.PUNC, ']')) {
        if (elements.length > 0) this.expect(TokenType.PUNC, ',');
        elements.push(this.parseExpression());
      }
      return { type: 'ArrayLiteral', elements };
    }

    // S-entropy literal: #(se, sk, st)
    if (tok.type === TokenType.PUNC && tok.value === '#') {
      this.advance();
      this.expect(TokenType.PUNC, '(');
      const se = this.parseExpression();
      this.expect(TokenType.PUNC, ',');
      const sk = this.parseExpression();
      this.expect(TokenType.PUNC, ',');
      const st = this.parseExpression();
      this.expect(TokenType.PUNC, ')');
      return { type: 'SEntropyLiteral', se, sk, st };
    }

    throw new SBSParseError(
      `Unexpected token ${tok.type} '${tok.value}'`,
      tok.line, tok.col,
    );
  }
}

export function parse(tokens: Token[]): { ast: Program; errors: SBSParseError[] } {
  const parser = new Parser(tokens);
  return parser.parse();
}
