import { TOKEN_TYPES } from './tokenizer';

class Parser {
  constructor(tokens) {
    this.tokens = tokens;
    this.pos = 0;
  }

  peek() { return this.tokens[this.pos]; }
  advance() { return this.tokens[this.pos++]; }

  expect(type, value) {
    const tok = this.advance();
    if (tok.type !== type || (value !== undefined && tok.value !== value)) {
      throw new Error(`Expected ${type}${value ? ` '${value}'` : ''} but got ${tok.type} '${tok.value}' at line ${tok.line}`);
    }
    return tok;
  }

  match(type, value) {
    const tok = this.peek();
    if (tok.type === type && (value === undefined || tok.value === value)) {
      return this.advance();
    }
    return null;
  }

  parse() {
    const program = { type: 'Program', body: [] };
    while (this.peek().type !== TOKEN_TYPES.EOF) {
      program.body.push(this.parseStatement());
    }
    return program;
  }

  parseStatement() {
    const tok = this.peek();

    if (tok.type === TOKEN_TYPES.KEYWORD) {
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
        default: break;
      }
    }

    const expr = this.parseExpression();
    this.match(TOKEN_TYPES.PUNC, ';');
    return { type: 'ExpressionStatement', expression: expr };
  }

  parseCircuitDecl() {
    this.expect(TOKEN_TYPES.KEYWORD, 'circuit');
    const name = this.expect(TOKEN_TYPES.IDENT).value;
    this.expect(TOKEN_TYPES.PUNC, '{');
    const body = [];
    while (!this.match(TOKEN_TYPES.PUNC, '}')) {
      body.push(this.parseStatement());
    }
    return { type: 'CircuitDecl', name, body };
  }

  parseNodeDecl() {
    this.expect(TOKEN_TYPES.KEYWORD, 'node');
    const name = this.expect(TOKEN_TYPES.IDENT).value;
    const props = this.parseProps();
    this.match(TOKEN_TYPES.PUNC, ';');
    return { type: 'NodeDecl', name, props };
  }

  parseEdgeDecl() {
    this.expect(TOKEN_TYPES.KEYWORD, 'edge');
    const src = this.expect(TOKEN_TYPES.IDENT).value;
    this.expect(TOKEN_TYPES.ARROW, '->');
    const dst = this.expect(TOKEN_TYPES.IDENT).value;
    const props = this.parseProps();
    this.match(TOKEN_TYPES.PUNC, ';');
    return { type: 'EdgeDecl', src, dst, props };
  }

  parseLetDecl() {
    this.expect(TOKEN_TYPES.KEYWORD, 'let');
    const name = this.expect(TOKEN_TYPES.IDENT).value;
    this.expect(TOKEN_TYPES.OP, '=');
    const init = this.parseExpression();
    this.match(TOKEN_TYPES.PUNC, ';');
    return { type: 'LetDecl', name, init };
  }

  parseFnDecl() {
    this.expect(TOKEN_TYPES.KEYWORD, 'fn');
    const name = this.expect(TOKEN_TYPES.IDENT).value;
    this.expect(TOKEN_TYPES.PUNC, '(');
    const params = [];
    while (!this.match(TOKEN_TYPES.PUNC, ')')) {
      if (params.length > 0) this.expect(TOKEN_TYPES.PUNC, ',');
      params.push(this.expect(TOKEN_TYPES.IDENT).value);
    }
    this.expect(TOKEN_TYPES.PUNC, '{');
    const body = [];
    while (!this.match(TOKEN_TYPES.PUNC, '}')) {
      body.push(this.parseStatement());
    }
    return { type: 'FnDecl', name, params, body };
  }

  parseObserve() {
    this.expect(TOKEN_TYPES.KEYWORD, 'observe');
    const target = this.parseExpression();
    this.match(TOKEN_TYPES.PUNC, ';');
    return { type: 'Observe', target };
  }

  parsePerturb() {
    this.expect(TOKEN_TYPES.KEYWORD, 'perturb');
    const target = this.parseExpression();
    const props = this.parseProps();
    this.match(TOKEN_TYPES.PUNC, ';');
    return { type: 'Perturb', target, props };
  }

  parseRestore() {
    this.expect(TOKEN_TYPES.KEYWORD, 'restore');
    const target = this.parseExpression();
    this.match(TOKEN_TYPES.PUNC, ';');
    return { type: 'Restore', target };
  }

  parseNavigate() {
    this.expect(TOKEN_TYPES.KEYWORD, 'navigate');
    const direction = this.match(TOKEN_TYPES.KEYWORD, 'from') ? 'backward' : 'forward';
    const target = this.parseExpression();
    this.match(TOKEN_TYPES.PUNC, ';');
    return { type: 'Navigate', direction, target };
  }

  parseCatalyst() {
    this.expect(TOKEN_TYPES.KEYWORD, 'catalyst');
    const name = this.expect(TOKEN_TYPES.IDENT).value;
    const props = this.parseProps();
    this.match(TOKEN_TYPES.PUNC, ';');
    return { type: 'CatalystDecl', name, props };
  }

  parseCascade() {
    this.expect(TOKEN_TYPES.KEYWORD, 'cascade');
    this.expect(TOKEN_TYPES.PUNC, '(');
    const catalysts = [];
    while (!this.match(TOKEN_TYPES.PUNC, ')')) {
      if (catalysts.length > 0) this.expect(TOKEN_TYPES.PUNC, ',');
      catalysts.push(this.parseExpression());
    }
    this.match(TOKEN_TYPES.PUNC, ';');
    return { type: 'Cascade', catalysts };
  }

  parseConvert() {
    this.expect(TOKEN_TYPES.KEYWORD, 'convert');
    const expr = this.parseExpression();
    this.expect(TOKEN_TYPES.KEYWORD, 'from');
    const from = this.expect(TOKEN_TYPES.KEYWORD).value;
    this.expect(TOKEN_TYPES.KEYWORD, 'to');
    const to = this.expect(TOKEN_TYPES.KEYWORD).value;
    this.match(TOKEN_TYPES.PUNC, ';');
    return { type: 'Convert', expr, from, to };
  }

  parseFor() {
    this.expect(TOKEN_TYPES.KEYWORD, 'for');
    const variable = this.expect(TOKEN_TYPES.IDENT).value;
    this.expect(TOKEN_TYPES.KEYWORD, 'in');
    const iterable = this.parseExpression();
    this.expect(TOKEN_TYPES.PUNC, '{');
    const body = [];
    while (!this.match(TOKEN_TYPES.PUNC, '}')) {
      body.push(this.parseStatement());
    }
    return { type: 'ForLoop', variable, iterable, body };
  }

  parseIf() {
    this.expect(TOKEN_TYPES.KEYWORD, 'if');
    const condition = this.parseExpression();
    this.expect(TOKEN_TYPES.PUNC, '{');
    const consequent = [];
    while (!this.match(TOKEN_TYPES.PUNC, '}')) {
      consequent.push(this.parseStatement());
    }
    let alternate = null;
    if (this.match(TOKEN_TYPES.KEYWORD, 'else')) {
      if (this.peek().value === 'if') {
        alternate = [this.parseIf()];
      } else {
        this.expect(TOKEN_TYPES.PUNC, '{');
        alternate = [];
        while (!this.match(TOKEN_TYPES.PUNC, '}')) {
          alternate.push(this.parseStatement());
        }
      }
    }
    return { type: 'IfStatement', condition, consequent, alternate };
  }

  parseImport() {
    this.expect(TOKEN_TYPES.KEYWORD, 'import');
    // import NAME from "source"  OR  import "module"
    const next = this.peek();
    if (next.type === TOKEN_TYPES.IDENT) {
      const name = this.advance().value;
      let alias = name;
      if (this.match(TOKEN_TYPES.KEYWORD, 'as')) {
        alias = this.expect(TOKEN_TYPES.IDENT).value;
      }
      this.expect(TOKEN_TYPES.KEYWORD, 'from');
      const source = this.expect(TOKEN_TYPES.STRING).value;
      this.match(TOKEN_TYPES.PUNC, ';');
      return { type: 'Import', name, alias, source };
    }
    const module = this.expect(TOKEN_TYPES.STRING).value;
    this.match(TOKEN_TYPES.PUNC, ';');
    return { type: 'Import', module };
  }

  parseExport() {
    this.expect(TOKEN_TYPES.KEYWORD, 'export');
    const decl = this.parseStatement();
    return { type: 'Export', declaration: decl };
  }

  parseProps() {
    if (!this.match(TOKEN_TYPES.PUNC, '{')) return {};
    const props = {};
    while (!this.match(TOKEN_TYPES.PUNC, '}')) {
      const tok = this.peek();
      let key;
      if (tok.type === TOKEN_TYPES.IDENT || tok.type === TOKEN_TYPES.KEYWORD) {
        key = this.advance().value;
      } else {
        throw new Error(`Expected property name but got ${tok.type} '${tok.value}' at line ${tok.line}`);
      }
      this.expect(TOKEN_TYPES.PUNC, ':');
      props[key] = this.parseExpression();
      this.match(TOKEN_TYPES.PUNC, ',');
    }
    return props;
  }

  parseExpression() {
    return this.parsePipe();
  }

  parsePipe() {
    let left = this.parseOr();
    while (this.match(TOKEN_TYPES.PIPE)) {
      const right = this.parseOr();
      left = { type: 'PipeExpr', left, right };
    }
    return left;
  }

  parseOr() {
    let left = this.parseAnd();
    while (this.match(TOKEN_TYPES.OP, '||')) {
      left = { type: 'BinaryExpr', op: '||', left, right: this.parseAnd() };
    }
    return left;
  }

  parseAnd() {
    let left = this.parseComparison();
    while (this.match(TOKEN_TYPES.OP, '&&')) {
      left = { type: 'BinaryExpr', op: '&&', left, right: this.parseComparison() };
    }
    return left;
  }

  parseComparison() {
    let left = this.parseAddSub();
    const ops = ['==', '!=', '<', '>', '<=', '>='];
    while (ops.includes(this.peek().value) && this.peek().type === TOKEN_TYPES.OP) {
      const op = this.advance().value;
      left = { type: 'BinaryExpr', op, left, right: this.parseAddSub() };
    }
    return left;
  }

  parseAddSub() {
    let left = this.parseMulDiv();
    while ((this.peek().value === '+' || this.peek().value === '-') && this.peek().type === TOKEN_TYPES.OP) {
      const op = this.advance().value;
      left = { type: 'BinaryExpr', op, left, right: this.parseMulDiv() };
    }
    return left;
  }

  parseMulDiv() {
    let left = this.parsePower();
    while (['*', '/', '%'].includes(this.peek().value) && this.peek().type === TOKEN_TYPES.OP) {
      const op = this.advance().value;
      left = { type: 'BinaryExpr', op, left, right: this.parsePower() };
    }
    return left;
  }

  parsePower() {
    let left = this.parseUnary();
    if (this.match(TOKEN_TYPES.OP, '**')) {
      left = { type: 'BinaryExpr', op: '**', left, right: this.parsePower() };
    }
    return left;
  }

  parseUnary() {
    if (this.peek().type === TOKEN_TYPES.OP && (this.peek().value === '-' || this.peek().value === '!')) {
      const op = this.advance().value;
      return { type: 'UnaryExpr', op, operand: this.parseUnary() };
    }
    return this.parsePostfix();
  }

  parsePostfix() {
    let expr = this.parsePrimary();
    while (true) {
      if (this.match(TOKEN_TYPES.PUNC, '.')) {
        const prop = this.expect(TOKEN_TYPES.IDENT).value;
        if (this.match(TOKEN_TYPES.PUNC, '(')) {
          const args = this.parseArgList();
          expr = { type: 'MethodCall', object: expr, method: prop, args };
        } else {
          expr = { type: 'MemberExpr', object: expr, property: prop };
        }
      } else if (this.match(TOKEN_TYPES.PUNC, '(')) {
        const args = this.parseArgList();
        expr = { type: 'CallExpr', callee: expr, args };
      } else if (this.match(TOKEN_TYPES.PUNC, '[')) {
        const index = this.parseExpression();
        this.expect(TOKEN_TYPES.PUNC, ']');
        expr = { type: 'IndexExpr', object: expr, index };
      } else {
        break;
      }
    }
    return expr;
  }

  parseArgList() {
    const args = [];
    while (!this.match(TOKEN_TYPES.PUNC, ')')) {
      if (args.length > 0) this.expect(TOKEN_TYPES.PUNC, ',');
      args.push(this.parseExpression());
    }
    return args;
  }

  parsePrimary() {
    const tok = this.peek();

    if (tok.type === TOKEN_TYPES.NUMBER) {
      this.advance();
      return { type: 'NumberLiteral', value: tok.value };
    }

    if (tok.type === TOKEN_TYPES.STRING) {
      this.advance();
      return { type: 'StringLiteral', value: tok.value };
    }

    if (tok.type === TOKEN_TYPES.KEYWORD && (tok.value === 'true' || tok.value === 'false')) {
      this.advance();
      return { type: 'BooleanLiteral', value: tok.value === 'true' };
    }

    if (tok.type === TOKEN_TYPES.KEYWORD && ['Se', 'Sk', 'St', 'R', 'V', 'floor', 'coherence', 'visibility'].includes(tok.value)) {
      this.advance();
      return { type: 'BuiltinRef', name: tok.value };
    }

    if (tok.type === TOKEN_TYPES.KEYWORD && tok.value === 'triple') {
      this.advance();
      this.expect(TOKEN_TYPES.PUNC, '(');
      const k = this.parseExpression();
      this.expect(TOKEN_TYPES.PUNC, ',');
      const t = this.parseExpression();
      this.expect(TOKEN_TYPES.PUNC, ',');
      const e = this.parseExpression();
      this.expect(TOKEN_TYPES.PUNC, ')');
      return { type: 'TripleExpr', k, t, e };
    }

    if (tok.type === TOKEN_TYPES.IDENT) {
      this.advance();
      return { type: 'Identifier', name: tok.value };
    }

    if (tok.type === TOKEN_TYPES.PUNC && tok.value === '(') {
      this.advance();
      const expr = this.parseExpression();
      this.expect(TOKEN_TYPES.PUNC, ')');
      return expr;
    }

    if (tok.type === TOKEN_TYPES.PUNC && tok.value === '[') {
      this.advance();
      const elements = [];
      while (!this.match(TOKEN_TYPES.PUNC, ']')) {
        if (elements.length > 0) this.expect(TOKEN_TYPES.PUNC, ',');
        elements.push(this.parseExpression());
      }
      return { type: 'ArrayLiteral', elements };
    }

    if (tok.type === TOKEN_TYPES.PUNC && tok.value === '#') {
      this.advance();
      this.expect(TOKEN_TYPES.PUNC, '(');
      const se = this.parseExpression();
      this.expect(TOKEN_TYPES.PUNC, ',');
      const sk = this.parseExpression();
      this.expect(TOKEN_TYPES.PUNC, ',');
      const st = this.parseExpression();
      this.expect(TOKEN_TYPES.PUNC, ')');
      return { type: 'SEntropyLiteral', se, sk, st };
    }

    throw new Error(`Unexpected token ${tok.type} '${tok.value}' at line ${tok.line}`);
  }
}

export function parse(tokens) {
  const parser = new Parser(tokens);
  return parser.parse();
}
