export { tokenize, KEYWORDS, SBSTokenError } from './tokenizer';
export { parse, Parser, SBSParseError } from './parser';
export { Emitter } from './emitter';
export { emitGLSL, emitJS } from './codegen';
export type { Token, TokenType, ASTNode, Expression, Program, CircuitDecl, NodeDecl, EdgeDecl, LetDecl, FnDecl, ObserveStmt, PerturbStmt, RestoreStmt, NavigateStmt, CatalystDecl, CascadeStmt, ConvertStmt, ForLoop, IfStatement, ImportStmt, ExportStmt, ExpressionStatement, PipeExpr, BinaryExpr, UnaryExpr, CallExpr, MethodCallExpr, MemberExpr, IndexExpr, TripleExpr, SEntropyLiteral, ArrayLiteral, Identifier, NumberLiteral, StringLiteral, BooleanLiteral, BuiltinRef, CircuitNode, CircuitEdge, Circuit, Perturbation, CatalystInfo, CompileError, CompileResult, } from './types';
import { CompileResult } from './types';
export declare function compileSBS(source: string): CompileResult;
export declare function validateSBS(source: string): {
    valid: boolean;
    errors: {
        message: string;
        line: number;
        col?: number;
    }[];
};
//# sourceMappingURL=index.d.ts.map