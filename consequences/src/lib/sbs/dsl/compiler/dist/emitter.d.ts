import { Program, Circuit, Perturbation, CompileError } from './types';
export declare class Emitter {
    private nodes;
    private edges;
    private variables;
    private functions;
    private catalysts;
    private circuits;
    readonly perturbations: Perturbation[];
    readonly observations: string[];
    readonly errors: CompileError[];
    readonly warnings: CompileError[];
    emit(program: Program): void;
    buildCircuit(): Circuit | null;
    private emitNode;
    private evalExpr;
    private evalProps;
    private findNode;
}
//# sourceMappingURL=emitter.d.ts.map