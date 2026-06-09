import { Token } from './types';
export declare const KEYWORDS: Set<string>;
export declare function tokenize(source: string): Token[];
export declare class SBSTokenError extends Error {
    line: number;
    col: number;
    constructor(message: string, line: number, col: number);
}
//# sourceMappingURL=tokenizer.d.ts.map