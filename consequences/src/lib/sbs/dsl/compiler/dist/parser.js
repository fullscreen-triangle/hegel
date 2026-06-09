"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Parser = exports.SBSParseError = void 0;
exports.parse = parse;
const types_1 = require("./types");
class SBSParseError extends Error {
    constructor(message, line, col) {
        super(`${message} at line ${line}, col ${col}`);
        this.name = 'SBSParseError';
        this.line = line;
        this.col = col;
    }
}
exports.SBSParseError = SBSParseError;
const RECOVERY_KEYWORDS = new Set([
    'circuit', 'node', 'edge', 'let', 'fn',
    'observe', 'perturb', 'restore', 'navigate',
    'catalyst', 'cascade', 'convert',
    'for', 'if', 'import', 'export',
]);
class Parser {
    constructor(tokens) {
        this.tokens = tokens;
        this.pos = 0;
        this.errors = [];
    }
    peek() {
        return this.tokens[this.pos];
    }
    advance() {
        return this.tokens[this.pos++];
    }
    expect(type, value) {
        const tok = this.advance();
        if (tok.type !== type || (value !== undefined && tok.value !== value)) {
            const expected = value ? `${type} '${value}'` : type;
            throw new SBSParseError(`Expected ${expected} but got ${tok.type} '${tok.value}'`, tok.line, tok.col);
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
    recover() {
        while (this.peek().type !== types_1.TokenType.EOF) {
            if (this.peek().type === types_1.TokenType.KEYWORD && RECOVERY_KEYWORDS.has(this.peek().value)) {
                return;
            }
            if (this.peek().type === types_1.TokenType.PUNC && this.peek().value === '}') {
                this.advance();
                return;
            }
            this.advance();
        }
    }
    parse() {
        const program = { type: 'Program', body: [] };
        while (this.peek().type !== types_1.TokenType.EOF) {
            try {
                program.body.push(this.parseStatement());
            }
            catch (err) {
                if (err instanceof SBSParseError) {
                    this.errors.push(err);
                    this.recover();
                }
                else {
                    throw err;
                }
            }
        }
        return { ast: program, errors: this.errors };
    }
    parseStatement() {
        const tok = this.peek();
        if (tok.type === types_1.TokenType.KEYWORD) {
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
        this.match(types_1.TokenType.PUNC, ';');
        return { type: 'ExpressionStatement', expression: expr };
    }
    parseCircuitDecl() {
        this.expect(types_1.TokenType.KEYWORD, 'circuit');
        const name = this.expect(types_1.TokenType.IDENT).value;
        this.expect(types_1.TokenType.PUNC, '{');
        const body = [];
        while (!this.match(types_1.TokenType.PUNC, '}')) {
            if (this.peek().type === types_1.TokenType.EOF) {
                throw new SBSParseError('Unterminated circuit block', this.peek().line, this.peek().col);
            }
            body.push(this.parseStatement());
        }
        return { type: 'CircuitDecl', name, body };
    }
    parseNodeDecl() {
        this.expect(types_1.TokenType.KEYWORD, 'node');
        const name = this.expect(types_1.TokenType.IDENT).value;
        const props = this.parseProps();
        this.match(types_1.TokenType.PUNC, ';');
        return { type: 'NodeDecl', name, props };
    }
    parseEdgeDecl() {
        this.expect(types_1.TokenType.KEYWORD, 'edge');
        const src = this.expect(types_1.TokenType.IDENT).value;
        this.expect(types_1.TokenType.ARROW, '->');
        const dst = this.expect(types_1.TokenType.IDENT).value;
        const props = this.parseProps();
        this.match(types_1.TokenType.PUNC, ';');
        return { type: 'EdgeDecl', src, dst, props };
    }
    parseLetDecl() {
        this.expect(types_1.TokenType.KEYWORD, 'let');
        const name = this.expect(types_1.TokenType.IDENT).value;
        this.expect(types_1.TokenType.OP, '=');
        const init = this.parseExpression();
        this.match(types_1.TokenType.PUNC, ';');
        return { type: 'LetDecl', name, init };
    }
    parseFnDecl() {
        this.expect(types_1.TokenType.KEYWORD, 'fn');
        const name = this.expect(types_1.TokenType.IDENT).value;
        this.expect(types_1.TokenType.PUNC, '(');
        const params = [];
        while (!this.match(types_1.TokenType.PUNC, ')')) {
            if (params.length > 0)
                this.expect(types_1.TokenType.PUNC, ',');
            params.push(this.expect(types_1.TokenType.IDENT).value);
        }
        this.expect(types_1.TokenType.PUNC, '{');
        const body = [];
        while (!this.match(types_1.TokenType.PUNC, '}')) {
            if (this.peek().type === types_1.TokenType.EOF) {
                throw new SBSParseError('Unterminated function block', this.peek().line, this.peek().col);
            }
            body.push(this.parseStatement());
        }
        return { type: 'FnDecl', name, params, body };
    }
    parseObserve() {
        this.expect(types_1.TokenType.KEYWORD, 'observe');
        const target = this.parseExpression();
        this.match(types_1.TokenType.PUNC, ';');
        return { type: 'Observe', target };
    }
    parsePerturb() {
        this.expect(types_1.TokenType.KEYWORD, 'perturb');
        const target = this.parseExpression();
        const props = this.parseProps();
        this.match(types_1.TokenType.PUNC, ';');
        return { type: 'Perturb', target, props };
    }
    parseRestore() {
        this.expect(types_1.TokenType.KEYWORD, 'restore');
        const target = this.parseExpression();
        this.match(types_1.TokenType.PUNC, ';');
        return { type: 'Restore', target };
    }
    parseNavigate() {
        this.expect(types_1.TokenType.KEYWORD, 'navigate');
        const direction = this.match(types_1.TokenType.KEYWORD, 'from') ? 'backward' : 'forward';
        const target = this.parseExpression();
        this.match(types_1.TokenType.PUNC, ';');
        return { type: 'Navigate', direction, target };
    }
    parseCatalyst() {
        this.expect(types_1.TokenType.KEYWORD, 'catalyst');
        const name = this.expect(types_1.TokenType.IDENT).value;
        const props = this.parseProps();
        this.match(types_1.TokenType.PUNC, ';');
        return { type: 'CatalystDecl', name, props };
    }
    parseCascade() {
        this.expect(types_1.TokenType.KEYWORD, 'cascade');
        this.expect(types_1.TokenType.PUNC, '(');
        const catalysts = [];
        while (!this.match(types_1.TokenType.PUNC, ')')) {
            if (catalysts.length > 0)
                this.expect(types_1.TokenType.PUNC, ',');
            catalysts.push(this.parseExpression());
        }
        this.match(types_1.TokenType.PUNC, ';');
        return { type: 'Cascade', catalysts };
    }
    parseConvert() {
        this.expect(types_1.TokenType.KEYWORD, 'convert');
        const expr = this.parseExpression();
        this.expect(types_1.TokenType.KEYWORD, 'from');
        const from = this.expect(types_1.TokenType.KEYWORD).value;
        this.expect(types_1.TokenType.KEYWORD, 'to');
        const to = this.expect(types_1.TokenType.KEYWORD).value;
        this.match(types_1.TokenType.PUNC, ';');
        return { type: 'Convert', expr, from, to };
    }
    parseFor() {
        this.expect(types_1.TokenType.KEYWORD, 'for');
        const variable = this.expect(types_1.TokenType.IDENT).value;
        this.expect(types_1.TokenType.KEYWORD, 'in');
        const iterable = this.parseExpression();
        this.expect(types_1.TokenType.PUNC, '{');
        const body = [];
        while (!this.match(types_1.TokenType.PUNC, '}')) {
            if (this.peek().type === types_1.TokenType.EOF) {
                throw new SBSParseError('Unterminated for block', this.peek().line, this.peek().col);
            }
            body.push(this.parseStatement());
        }
        return { type: 'ForLoop', variable, iterable, body };
    }
    parseIf() {
        this.expect(types_1.TokenType.KEYWORD, 'if');
        const condition = this.parseExpression();
        this.expect(types_1.TokenType.PUNC, '{');
        const consequent = [];
        while (!this.match(types_1.TokenType.PUNC, '}')) {
            if (this.peek().type === types_1.TokenType.EOF) {
                throw new SBSParseError('Unterminated if block', this.peek().line, this.peek().col);
            }
            consequent.push(this.parseStatement());
        }
        let alternate = null;
        if (this.match(types_1.TokenType.KEYWORD, 'else')) {
            if (this.peek().value === 'if') {
                alternate = [this.parseIf()];
            }
            else {
                this.expect(types_1.TokenType.PUNC, '{');
                alternate = [];
                while (!this.match(types_1.TokenType.PUNC, '}')) {
                    if (this.peek().type === types_1.TokenType.EOF) {
                        throw new SBSParseError('Unterminated else block', this.peek().line, this.peek().col);
                    }
                    alternate.push(this.parseStatement());
                }
            }
        }
        return { type: 'IfStatement', condition, consequent, alternate };
    }
    parseImport() {
        this.expect(types_1.TokenType.KEYWORD, 'import');
        const name = this.expect(types_1.TokenType.IDENT).value;
        let alias = null;
        if (this.match(types_1.TokenType.KEYWORD, 'as')) {
            alias = this.expect(types_1.TokenType.IDENT).value;
        }
        this.expect(types_1.TokenType.KEYWORD, 'from');
        const source = this.expect(types_1.TokenType.STRING).value;
        this.match(types_1.TokenType.PUNC, ';');
        return { type: 'Import', name, alias, source };
    }
    parseExport() {
        this.expect(types_1.TokenType.KEYWORD, 'export');
        const declaration = this.parseStatement();
        return { type: 'Export', declaration };
    }
    parseProps() {
        if (!this.match(types_1.TokenType.PUNC, '{'))
            return {};
        const props = {};
        while (!this.match(types_1.TokenType.PUNC, '}')) {
            if (this.peek().type === types_1.TokenType.EOF) {
                throw new SBSParseError('Unterminated property block', this.peek().line, this.peek().col);
            }
            const key = this.expect(types_1.TokenType.IDENT).value;
            this.expect(types_1.TokenType.PUNC, ':');
            props[key] = this.parseExpression();
            this.match(types_1.TokenType.PUNC, ',');
        }
        return props;
    }
    // ── Expression parsing (precedence climbing) ──
    parseExpression() {
        return this.parsePipe();
    }
    parsePipe() {
        let left = this.parseOr();
        while (this.match(types_1.TokenType.PIPE)) {
            const right = this.parseOr();
            left = { type: 'PipeExpr', left, right };
        }
        return left;
    }
    parseOr() {
        let left = this.parseAnd();
        while (this.match(types_1.TokenType.OP, '||')) {
            left = { type: 'BinaryExpr', op: '||', left, right: this.parseAnd() };
        }
        return left;
    }
    parseAnd() {
        let left = this.parseComparison();
        while (this.match(types_1.TokenType.OP, '&&')) {
            left = { type: 'BinaryExpr', op: '&&', left, right: this.parseComparison() };
        }
        return left;
    }
    parseComparison() {
        let left = this.parseAddSub();
        const compOps = new Set(['==', '!=', '<', '>', '<=', '>=']);
        while (this.peek().type === types_1.TokenType.OP && compOps.has(this.peek().value)) {
            const op = this.advance().value;
            left = { type: 'BinaryExpr', op, left, right: this.parseAddSub() };
        }
        return left;
    }
    parseAddSub() {
        let left = this.parseMulDiv();
        while (this.peek().type === types_1.TokenType.OP && (this.peek().value === '+' || this.peek().value === '-')) {
            const op = this.advance().value;
            left = { type: 'BinaryExpr', op, left, right: this.parseMulDiv() };
        }
        return left;
    }
    parseMulDiv() {
        let left = this.parsePower();
        while (this.peek().type === types_1.TokenType.OP && (this.peek().value === '*' || this.peek().value === '/' || this.peek().value === '%')) {
            const op = this.advance().value;
            left = { type: 'BinaryExpr', op, left, right: this.parsePower() };
        }
        return left;
    }
    parsePower() {
        let left = this.parseUnary();
        if (this.match(types_1.TokenType.OP, '**')) {
            // right-associative
            left = { type: 'BinaryExpr', op: '**', left, right: this.parsePower() };
        }
        return left;
    }
    parseUnary() {
        if (this.peek().type === types_1.TokenType.OP && (this.peek().value === '-' || this.peek().value === '!')) {
            const op = this.advance().value;
            return { type: 'UnaryExpr', op, operand: this.parseUnary() };
        }
        return this.parsePostfix();
    }
    parsePostfix() {
        let expr = this.parsePrimary();
        while (true) {
            if (this.match(types_1.TokenType.PUNC, '.')) {
                const prop = this.expect(types_1.TokenType.IDENT).value;
                if (this.match(types_1.TokenType.PUNC, '(')) {
                    const args = this.parseArgList();
                    expr = { type: 'MethodCall', object: expr, method: prop, args };
                }
                else {
                    expr = { type: 'MemberExpr', object: expr, property: prop };
                }
            }
            else if (this.match(types_1.TokenType.PUNC, '(')) {
                const args = this.parseArgList();
                expr = { type: 'CallExpr', callee: expr, args };
            }
            else if (this.match(types_1.TokenType.PUNC, '[')) {
                const index = this.parseExpression();
                this.expect(types_1.TokenType.PUNC, ']');
                expr = { type: 'IndexExpr', object: expr, index };
            }
            else {
                break;
            }
        }
        return expr;
    }
    parseArgList() {
        const args = [];
        while (!this.match(types_1.TokenType.PUNC, ')')) {
            if (args.length > 0)
                this.expect(types_1.TokenType.PUNC, ',');
            args.push(this.parseExpression());
        }
        return args;
    }
    parsePrimary() {
        const tok = this.peek();
        if (tok.type === types_1.TokenType.NUMBER) {
            this.advance();
            return { type: 'NumberLiteral', value: tok.value };
        }
        if (tok.type === types_1.TokenType.STRING) {
            this.advance();
            return { type: 'StringLiteral', value: tok.value };
        }
        if (tok.type === types_1.TokenType.KEYWORD && (tok.value === 'true' || tok.value === 'false')) {
            this.advance();
            return { type: 'BooleanLiteral', value: tok.value === 'true' };
        }
        const builtins = new Set(['Se', 'Sk', 'St', 'R', 'V', 'floor', 'coherence', 'visibility']);
        if (tok.type === types_1.TokenType.KEYWORD && builtins.has(tok.value)) {
            this.advance();
            return { type: 'BuiltinRef', name: tok.value };
        }
        if (tok.type === types_1.TokenType.KEYWORD && tok.value === 'triple') {
            this.advance();
            this.expect(types_1.TokenType.PUNC, '(');
            const k = this.parseExpression();
            this.expect(types_1.TokenType.PUNC, ',');
            const t = this.parseExpression();
            this.expect(types_1.TokenType.PUNC, ',');
            const e = this.parseExpression();
            this.expect(types_1.TokenType.PUNC, ')');
            return { type: 'TripleExpr', k, t, e };
        }
        if (tok.type === types_1.TokenType.IDENT) {
            this.advance();
            return { type: 'Identifier', name: tok.value };
        }
        if (tok.type === types_1.TokenType.PUNC && tok.value === '(') {
            this.advance();
            const expr = this.parseExpression();
            this.expect(types_1.TokenType.PUNC, ')');
            return expr;
        }
        if (tok.type === types_1.TokenType.PUNC && tok.value === '[') {
            this.advance();
            const elements = [];
            while (!this.match(types_1.TokenType.PUNC, ']')) {
                if (elements.length > 0)
                    this.expect(types_1.TokenType.PUNC, ',');
                elements.push(this.parseExpression());
            }
            return { type: 'ArrayLiteral', elements };
        }
        // S-entropy literal: #(se, sk, st)
        if (tok.type === types_1.TokenType.PUNC && tok.value === '#') {
            this.advance();
            this.expect(types_1.TokenType.PUNC, '(');
            const se = this.parseExpression();
            this.expect(types_1.TokenType.PUNC, ',');
            const sk = this.parseExpression();
            this.expect(types_1.TokenType.PUNC, ',');
            const st = this.parseExpression();
            this.expect(types_1.TokenType.PUNC, ')');
            return { type: 'SEntropyLiteral', se, sk, st };
        }
        throw new SBSParseError(`Unexpected token ${tok.type} '${tok.value}'`, tok.line, tok.col);
    }
}
exports.Parser = Parser;
function parse(tokens) {
    const parser = new Parser(tokens);
    return parser.parse();
}
//# sourceMappingURL=parser.js.map