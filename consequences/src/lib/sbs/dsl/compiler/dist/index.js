"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.emitJS = exports.emitGLSL = exports.Emitter = exports.SBSParseError = exports.Parser = exports.parse = exports.SBSTokenError = exports.KEYWORDS = exports.tokenize = void 0;
exports.compileSBS = compileSBS;
exports.validateSBS = validateSBS;
var tokenizer_1 = require("./tokenizer");
Object.defineProperty(exports, "tokenize", { enumerable: true, get: function () { return tokenizer_1.tokenize; } });
Object.defineProperty(exports, "KEYWORDS", { enumerable: true, get: function () { return tokenizer_1.KEYWORDS; } });
Object.defineProperty(exports, "SBSTokenError", { enumerable: true, get: function () { return tokenizer_1.SBSTokenError; } });
var parser_1 = require("./parser");
Object.defineProperty(exports, "parse", { enumerable: true, get: function () { return parser_1.parse; } });
Object.defineProperty(exports, "Parser", { enumerable: true, get: function () { return parser_1.Parser; } });
Object.defineProperty(exports, "SBSParseError", { enumerable: true, get: function () { return parser_1.SBSParseError; } });
var emitter_1 = require("./emitter");
Object.defineProperty(exports, "Emitter", { enumerable: true, get: function () { return emitter_1.Emitter; } });
var codegen_1 = require("./codegen");
Object.defineProperty(exports, "emitGLSL", { enumerable: true, get: function () { return codegen_1.emitGLSL; } });
Object.defineProperty(exports, "emitJS", { enumerable: true, get: function () { return codegen_1.emitJS; } });
const tokenizer_2 = require("./tokenizer");
const parser_2 = require("./parser");
const emitter_2 = require("./emitter");
const codegen_2 = require("./codegen");
function compileSBS(source) {
    const emitter = new emitter_2.Emitter();
    try {
        const tokens = (0, tokenizer_2.tokenize)(source);
        const { ast, errors: parseErrors } = (0, parser_2.parse)(tokens);
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
            glsl: circuit ? (0, codegen_2.emitGLSL)(circuit) : null,
            js: circuit ? (0, codegen_2.emitJS)(circuit, emitter.perturbations) : null,
        };
    }
    catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        const line = err.line ?? 0;
        const col = err.col ?? 0;
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
function validateSBS(source) {
    try {
        const tokens = (0, tokenizer_2.tokenize)(source);
        const { errors } = (0, parser_2.parse)(tokens);
        return {
            valid: errors.length === 0,
            errors: errors.map(e => ({ message: e.message, line: e.line, col: e.col })),
        };
    }
    catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        const line = err.line ?? 0;
        return { valid: false, errors: [{ message: msg, line }] };
    }
}
//# sourceMappingURL=index.js.map