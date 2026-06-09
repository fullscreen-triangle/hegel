export declare const TokenType: {
    readonly KEYWORD: "KEYWORD";
    readonly IDENT: "IDENT";
    readonly NUMBER: "NUMBER";
    readonly STRING: "STRING";
    readonly OP: "OP";
    readonly PUNC: "PUNC";
    readonly ARROW: "ARROW";
    readonly PIPE: "PIPE";
    readonly EOF: "EOF";
};
export type TokenType = typeof TokenType[keyof typeof TokenType];
export interface Token {
    type: TokenType;
    value: string | number | null;
    line: number;
    col: number;
}
export type ASTNode = Program | CircuitDecl | NodeDecl | EdgeDecl | LetDecl | FnDecl | ObserveStmt | PerturbStmt | RestoreStmt | NavigateStmt | CatalystDecl | CascadeStmt | ConvertStmt | ForLoop | IfStatement | ImportStmt | ExportStmt | ExpressionStatement;
export type Expression = PipeExpr | BinaryExpr | UnaryExpr | CallExpr | MethodCallExpr | MemberExpr | IndexExpr | TripleExpr | SEntropyLiteral | ArrayLiteral | Identifier | NumberLiteral | StringLiteral | BooleanLiteral | BuiltinRef;
export interface Program {
    type: 'Program';
    body: ASTNode[];
}
export interface CircuitDecl {
    type: 'CircuitDecl';
    name: string;
    body: ASTNode[];
}
export interface NodeDecl {
    type: 'NodeDecl';
    name: string;
    props: Record<string, Expression>;
}
export interface EdgeDecl {
    type: 'EdgeDecl';
    src: string;
    dst: string;
    props: Record<string, Expression>;
}
export interface LetDecl {
    type: 'LetDecl';
    name: string;
    init: Expression;
}
export interface FnDecl {
    type: 'FnDecl';
    name: string;
    params: string[];
    body: ASTNode[];
}
export interface ObserveStmt {
    type: 'Observe';
    target: Expression;
}
export interface PerturbStmt {
    type: 'Perturb';
    target: Expression;
    props: Record<string, Expression>;
}
export interface RestoreStmt {
    type: 'Restore';
    target: Expression;
}
export interface NavigateStmt {
    type: 'Navigate';
    direction: 'forward' | 'backward';
    target: Expression;
}
export interface CatalystDecl {
    type: 'CatalystDecl';
    name: string;
    props: Record<string, Expression>;
}
export interface CascadeStmt {
    type: 'Cascade';
    catalysts: Expression[];
}
export interface ConvertStmt {
    type: 'Convert';
    expr: Expression;
    from: string;
    to: string;
}
export interface ForLoop {
    type: 'ForLoop';
    variable: string;
    iterable: Expression;
    body: ASTNode[];
}
export interface IfStatement {
    type: 'IfStatement';
    condition: Expression;
    consequent: ASTNode[];
    alternate: ASTNode[] | null;
}
export interface ImportStmt {
    type: 'Import';
    name: string;
    alias: string | null;
    source: string;
}
export interface ExportStmt {
    type: 'Export';
    declaration: ASTNode;
}
export interface ExpressionStatement {
    type: 'ExpressionStatement';
    expression: Expression;
}
export interface PipeExpr {
    type: 'PipeExpr';
    left: Expression;
    right: Expression;
}
export interface BinaryExpr {
    type: 'BinaryExpr';
    op: string;
    left: Expression;
    right: Expression;
}
export interface UnaryExpr {
    type: 'UnaryExpr';
    op: string;
    operand: Expression;
}
export interface CallExpr {
    type: 'CallExpr';
    callee: Expression;
    args: Expression[];
}
export interface MethodCallExpr {
    type: 'MethodCall';
    object: Expression;
    method: string;
    args: Expression[];
}
export interface MemberExpr {
    type: 'MemberExpr';
    object: Expression;
    property: string;
}
export interface IndexExpr {
    type: 'IndexExpr';
    object: Expression;
    index: Expression;
}
export interface TripleExpr {
    type: 'TripleExpr';
    k: Expression;
    t: Expression;
    e: Expression;
}
export interface SEntropyLiteral {
    type: 'SEntropyLiteral';
    se: Expression;
    sk: Expression;
    st: Expression;
}
export interface ArrayLiteral {
    type: 'ArrayLiteral';
    elements: Expression[];
}
export interface Identifier {
    type: 'Identifier';
    name: string;
}
export interface NumberLiteral {
    type: 'NumberLiteral';
    value: number;
}
export interface StringLiteral {
    type: 'StringLiteral';
    value: string;
}
export interface BooleanLiteral {
    type: 'BooleanLiteral';
    value: boolean;
}
export interface BuiltinRef {
    type: 'BuiltinRef';
    name: string;
}
export interface CircuitNode {
    id: number;
    name: string;
    speciesId: string;
    compartment: string;
    compartmentName: string;
    concentration: number;
    mu0: number;
    mu: number;
    boundary: boolean;
}
export interface CircuitEdge {
    id: number;
    name: string;
    reactionId: string;
    src: number;
    dst: number;
    rate: number;
    conductance: number;
    deltaG: number;
}
export interface Circuit {
    nodes: CircuitNode[];
    edges: CircuitEdge[];
    compartments: string[];
    modelId: string;
    numNodes: number;
    numEdges: number;
}
export interface Perturbation {
    target: string;
    factor: number;
    edge?: string;
}
export interface CatalystInfo {
    power: number;
    target: string | null;
}
export interface CompileError {
    message: string;
    line: number;
    col?: number;
}
export interface CompileResult {
    success: boolean;
    ast?: Program;
    circuit: Circuit | null;
    perturbations: Perturbation[];
    observations: string[];
    errors: CompileError[];
    warnings: CompileError[];
    glsl: string | null;
    js: string | null;
}
//# sourceMappingURL=types.d.ts.map