import { Token, Program } from './types';
export declare class SBSParseError extends Error {
    line: number;
    col: number;
    constructor(message: string, line: number, col: number);
}
export declare class Parser {
    private tokens;
    private pos;
    private errors;
    constructor(tokens: Token[]);
    private peek;
    private advance;
    private expect;
    private match;
    private recover;
    parse(): {
        ast: Program;
        errors: SBSParseError[];
    };
    private parseStatement;
    private parseCircuitDecl;
    private parseNodeDecl;
    private parseEdgeDecl;
    private parseLetDecl;
    private parseFnDecl;
    private parseObserve;
    private parsePerturb;
    private parseRestore;
    private parseNavigate;
    private parseCatalyst;
    private parseCascade;
    private parseConvert;
    private parseFor;
    private parseIf;
    private parseImport;
    private parseExport;
    private parseProps;
    private parseExpression;
    private parsePipe;
    private parseOr;
    private parseAnd;
    private parseComparison;
    private parseAddSub;
    private parseMulDiv;
    private parsePower;
    private parseUnary;
    private parsePostfix;
    private parseArgList;
    private parsePrimary;
}
export declare function parse(tokens: Token[]): {
    ast: Program;
    errors: SBSParseError[];
};
//# sourceMappingURL=parser.d.ts.map