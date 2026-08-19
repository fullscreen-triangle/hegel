// The eleven plans the validation suite ships, read from
// ckg/validation-federated/plans/ at authoring time. They are presets and not
// fixtures: the notebook executes them through the same interpreter, so a
// preset that stopped agreeing with the suite would show a different verdict
// here rather than silently diverge.

export const PRESETS = [
  {
    id: "budget_trap",
    source: "# c_1 = c_2 = 1 and budget = 2, so B >= sum c_i. Step 1 returns cardinality 3,\n# so step 2's realised cost is 3 and only 1 request remains: (R3) refuses.\n# prop:necessary-not-sufficient: the c_i are minima over inputs, and the\n# realised input is not the minimising one.\nplan budget_trap {\n  budget 2 requests\n\n  let roots = from tiny_onto\n      ask descendants_of(\"CHEBI:1\")\n      within 1\n\n  let rxns  = from tiny_graph\n      ask reactions_consuming(?c)\n      with ?c in roots\n      within 1\n\n  emit rxns\n}",
  },
  {
    id: "empty_answer",
    source: "# The request is well-formed, affordable and answered; the corpus simply has\n# no producing reaction for these compounds. (R5) fires, and def:blocker\n# assigns no blocker -- the JSON omits the key entirely.\nplan empty_answer {\n  budget 40 requests\n\n  let seeds = from chebi\n      ask descendants_of(\"CHEBI:3\")\n      within 4\n\n  let kegg  = map seeds via chebi2kegg\n      expect partial 0.1\n\n  let none  = from rhea\n      ask reactions_producing(?c)\n      with ?c in kegg\n      within 20\n\n  emit none\n}",
  },
  {
    id: "enzymes_in_shared_pathways",
    source: "# lst:plan of part2-language.tex, verbatim.\nplan enzymes_in_shared_pathways {\n  budget 400 requests\n\n  let acids = from CHEBI\n      ask descendants_of(\"CHEBI:35238\")\n      within 20\n\n  let rxns  = from RHEA\n      ask reactions_consuming(?c)\n      with ?c in acids\n      within 120\n      else fail unresolved\n\n  let ecs   = from RHEA\n      ask enzyme_of(?r)\n      with ?r in rxns\n      within 60\n\n  let kids  = map ecs via ec_to_kegg\n      expect partial 0.6\n\n  let paths = from KEGG\n      ask link(\"pathway\", ?k)\n      with ?k in kids\n      within 200\n      when starved emit partial\n\n  emit paths with provenance\n}",
  },
  {
    id: "healthy_chain",
    source: "# Identical to starved_chain except the declared expectation. That single\n# difference is what thm:six requires: configurations differing in one respect.\nplan healthy_chain {\n  budget 200 requests\n\n  let acids = from chebi\n      ask descendants_of(\"CHEBI:1\")\n      within 10\n\n  let kegg  = map acids via chebi2kegg\n      expect partial 0.6\n\n  let rxns  = from rhea\n      ask reactions_consuming(?c)\n      with ?c in kegg\n      within 60\n\n  emit rxns\n}",
  },
  {
    id: "ill_capability",
    source: "# The lookup source declares {lookup, link} and NOT pattern. Asking it for a\n# conjunctive pattern is ill-capability, so thm:static refuses before contact:\n# (V1) checks requests_issued is still zero after the refusal.\nplan ill_capability {\n  budget 100 requests\n\n  let seed = from chebi\n      ask descendants_of(\"CHEBI:1\")\n      within 4\n\n  let bad  = from enzdb\n      ask reactions_consuming(?c)\n      with ?c in seed\n      within 10\n\n  emit bad\n}",
  },
  {
    id: "order_a",
    source: "# Filter before expansion. KEGG:C10 consumes nothing, so dropping it costs no\n# coverage; removing it before the expansion saves the request the expansion\n# would spend on it. The filter names the identifier rather than a label,\n# because chebi2kegg is non-injective -- CHEBI:9 and CHEBI:10 both reach\n# KEGG:C9 -- and the surviving row's attributes are whichever preimage was\n# merged last. Only the identifier is reliable after such a map.\nplan order_a {\n  budget 400 requests\n\n  let acids = from chebi\n      ask descendants_of(\"CHEBI:1\")\n      within 10\n\n  let kegg  = map acids via chebi2kegg\n      expect partial 0.1\n\n  let narrow = filter kegg where _id != \"KEGG:C10\"\n\n  let rxns  = from rhea\n      ask reactions_consuming(?c)\n      with ?c in narrow\n      within 60\n\n  emit rxns\n}",
  },
  {
    id: "order_b",
    source: "# Expand before filtering. Identical coverage to order_a -- the discarded\n# elements contribute nothing downstream -- at a higher request count, because\n# the expansion is charged on the unfiltered input. (V10): the plan language\n# makes the ordering a decision the author states, not one a query planner\n# takes silently.\nplan order_b {\n  budget 400 requests\n\n  let acids = from chebi\n      ask descendants_of(\"CHEBI:1\")\n      within 10\n\n  let kegg  = map acids via chebi2kegg\n      expect partial 0.1\n\n  let rxns  = from rhea\n      ask reactions_consuming(?c)\n      with ?c in kegg\n      within 60\n\n  let narrow = filter rxns where _from != \"KEGG:C10\"\n\n  emit narrow\n}",
  },
  {
    id: "routes",
    source: "# lst:routes of part4-translation.tex, verbatim inside a plan wrapper.\n# The listing in the paper is a fragment; the header and budget are the\n# minimum a parseable plan needs and add nothing the fragment did not say.\nplan parallel_routes {\n  budget 40 requests\n\n  let compounds = from CHEBI\n      ask descendants_of(\"CHEBI:1\")\n      within 4\n\n  let direct   = map compounds via chebi_to_kegg\n  let indirect = map compounds via chebi_to_inchikey\n                 then via inchikey_to_kegg\n\n  let both     = union direct indirect\n  assert soundness(direct) and soundness(indirect)\n  emit divergence(direct, indirect) as resolved_extent\n}",
  },
  {
    id: "single_step",
    source: "# m = 1. There is no predecessor, so (R1) cannot fire: prop:starve-reachable(a)\n# says starved is unreachable here whatever the fixture does.\nplan single_step {\n  budget 20 requests\n\n  let acids = from chebi\n      ask descendants_of(\"CHEBI:1\")\n      within 8\n\n  emit acids\n}",
  },
  {
    id: "starved_chain",
    source: "# m = 3. The map retains 7/9 end to end but the declared expectation is 0.9,\n# so def:retention-check returns starved; the successor then starves by (R1)\n# and prop:blame terminates at the map step in two hops.\nplan starved_chain {\n  budget 200 requests\n\n  let acids = from chebi\n      ask descendants_of(\"CHEBI:1\")\n      within 10\n\n  let kegg  = map acids via chebi2kegg\n      expect partial 0.9\n\n  let rxns  = from rhea\n      ask reactions_consuming(?c)\n      with ?c in kegg\n      within 60\n\n  emit rxns\n}",
  },
  {
    id: "step_timeout",
    source: "# The plan can afford the step; the step's own `within` cannot. (R4) fires and\n# def:blocker assigns `engine`, distinct from the `budget` of (R3).\nplan step_timeout {\n  budget 400 requests\n\n  let acids = from chebi\n      ask descendants_of(\"CHEBI:1\")\n      within 10\n\n  let kegg  = map acids via chebi2kegg\n      expect partial 0.1\n\n  let rxns  = from rhea\n      ask reactions_consuming(?c)\n      with ?c in kegg\n      within 2\n\n  emit rxns\n}",
  },
];

export default PRESETS;
