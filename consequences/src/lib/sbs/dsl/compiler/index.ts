export { tokenize, KEYWORDS, SBSTokenError } from './tokenizer';
export { parse, Parser, SBSParseError } from './parser';
export { Emitter } from './emitter';
export { emitGLSL, emitJS } from './codegen';

export type {
  Token, TokenType,
  ASTNode, Expression, Program,
  CircuitDecl, NodeDecl, EdgeDecl, LetDecl, FnDecl,
  ObserveStmt, PerturbStmt, RestoreStmt, NavigateStmt,
  CatalystDecl, CascadeStmt, ConvertStmt,
  ForLoop, IfStatement, ImportStmt, ExportStmt,
  ExpressionStatement,
  PipeExpr, BinaryExpr, UnaryExpr, CallExpr, MethodCallExpr,
  MemberExpr, IndexExpr, TripleExpr, SEntropyLiteral,
  ArrayLiteral, Identifier, NumberLiteral, StringLiteral,
  BooleanLiteral, BuiltinRef,
  CircuitNode, CircuitEdge, Circuit,
  Perturbation, CatalystInfo,
  CompileError, CompileResult,
} from './types';

import { tokenize } from './tokenizer';
import { parse, SBSParseError } from './parser';
import { Emitter } from './emitter';
import { emitGLSL, emitJS } from './codegen';
import { CompileResult } from './types';

export function compileSBS(source: string): CompileResult {
  const emitter = new Emitter();

  try {
    const tokens = tokenize(source);
    const { ast, errors: parseErrors } = parse(tokens);

    if (parseErrors.length > 0) {
      return {
        success: false,
        ast,
        circuit: null,
        perturbations: [],
        observations: [],
        errors: parseErrors.map(e => ({ message: e.message, line: e.line, col: e.col })),
        warnings: [],
        glsl: null,
        js: null,
      };
    }

    emitter.emit(ast);
    const circuit = emitter.buildCircuit();

    return {
      success: emitter.errors.length === 0,
      ast,
      circuit,
      perturbations: emitter.perturbations,
      observations: emitter.observations,
      errors: emitter.errors,
      warnings: emitter.warnings,
      glsl: circuit ? emitGLSL(circuit) : null,
      js: circuit ? emitJS(circuit, emitter.perturbations) : null,
    };
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    const line = (err as { line?: number }).line ?? 0;
    const col = (err as { col?: number }).col ?? 0;
    return {
      success: false,
      circuit: null,
      perturbations: [],
      observations: [],
      errors: [{ message: msg, line, col }],
      warnings: [],
      glsl: null,
      js: null,
    };
  }
}

export function validateSBS(source: string): { valid: boolean; errors: { message: string; line: number; col?: number }[] } {
  try {
    const tokens = tokenize(source);
    const { errors } = parse(tokens);
    return {
      valid: errors.length === 0,
      errors: errors.map(e => ({ message: e.message, line: e.line, col: e.col })),
    };
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    const line = (err as { line?: number }).line ?? 0;
    return { valid: false, errors: [{ message: msg, line }] };
  }
}
