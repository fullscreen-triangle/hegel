"""The biocatalysis world: sources shaped so Doerr's five questions differ.

Everything here is local and hand-checkable, on the same terms as `build.py`.
The point of the fixture is not that it is realistic -- it is deliberately
tiny -- but that its *shape* reproduces the structural facts that make the
five questions hard, so that a verdict the executor returns is a consequence
of the world's structure and not of a value chosen to produce it.

Five sources across four namespaces, because the questions genuinely cross
them:

  TAX    organism taxonomy .......... an ontology; `path`, no `neg`
  RXN    reactions and enzymes ...... a graph store; `pattern`, `neg`, no `agg`
  SEQ    protein sequences .......... keyed sequences; `regex`, no `pattern`
  PROV   activity provenance ........ a graph store: operator, date, device
  INST   instrument records ......... a flat REST stand-in; `lookup` only

Four facts about this world are load-bearing, and each is an honest
declaration in the sense of def:source rather than a convenience:

(1) SEQ does not declare `pattern`. A sequence store reached by accession
    cannot enumerate its own extent, so a scan over an unbound set is not
    something it can do. Q1's residue clause is therefore only answerable
    when an earlier step supplies the accessions -- which is precisely why
    Q1 is a plan and not a query.

(2) RXN does not declare `agg`. The deployment materialises at most a fixed
    number of rows before aggregating, so a COUNT over a large extent would
    return a well-formed wrong number. prop:under says the honest response
    is to withhold `agg` even though the endpoint would answer, and even
    though SPARQL has COUNT. There is no place in an ontology + reasoner
    stack to record that a supported operation must not be trusted.

(3) INST does not declare `pattern`. "Which devices are Bruker
    spectrometers" is a scan over an extent a keyed record service does not
    expose, and three of Doerr's eight generic queries are phrased exactly
    that way. thm:static refuses them by name, before contact.

(4) The reaction store and the sequence store are keyed alike but the map
    between them is partial: one of the five transaminases has no sequence
    entry. That is not an error in the fixture; it is what a federation
    looks like, and it is the difference between "no enzyme satisfies your
    constraint" and "one candidate was never examined". A SPARQL result set
    has no room for the third outcome (cor:onebit).
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from hfq import (LookupAdapter, MapAdapter, OntologyAdapter, Registry,
                 TranslationMap, featureset)
from hfq.biocat import FilteringGraphAdapter, ProvenanceAdapter, SequenceAdapter

SNAPSHOT = "biocat-v1"


# ---------------------------------------------------------------------------
# TAX -- organism taxonomy
# ---------------------------------------------------------------------------

#: Two kingdoms under a shared root, which is what makes Q1's "from a
#: bacterium, not a eukaryote" a `neg` and not merely a second `pattern`:
#: the question is answered by a set difference over a closure, and a source
#: that computes the closure but not the difference must say so.
TAX_PARENTS: Dict[str, List[str]] = {
    "TAX:Bacteria":       ["TAX:cellular"],
    "TAX:Eukaryota":      ["TAX:cellular"],
    "TAX:Firmicutes":     ["TAX:Bacteria"],
    "TAX:Proteobacteria": ["TAX:Bacteria"],
    "TAX:Fungi":          ["TAX:Eukaryota"],
    "TAX:Bsubtilis":      ["TAX:Firmicutes"],
    "TAX:Cviolaceum":     ["TAX:Proteobacteria"],
    "TAX:Pfluorescens":   ["TAX:Proteobacteria"],
    "TAX:Acerevisiae":    ["TAX:Fungi"],
    "TAX:Ccrenatus":      ["TAX:Fungi"],
}

TAX_LABELS = {
    "TAX:Bsubtilis":      "Bacillus subtilis",
    "TAX:Cviolaceum":     "Chromobacterium violaceum",
    "TAX:Pfluorescens":   "Pseudomonas fluorescens",
    "TAX:Acerevisiae":    "Saccharomyces cerevisiae",
    "TAX:Ccrenatus":      "Candida crenatus",
    "TAX:Bacteria":       "Bacteria",
    "TAX:Eukaryota":      "Eukaryota",
    "TAX:Firmicutes":     "Firmicutes",
    "TAX:Proteobacteria": "Proteobacteria",
    "TAX:Fungi":          "Fungi",
}


# ---------------------------------------------------------------------------
# RXN -- reactions, enzymes, organisms
# ---------------------------------------------------------------------------

#: Five transaminases on the benzylethylamine reaction. Three bacterial with
#: sequences, one eukaryotic, one bacterial whose sequence source holds no
#: entry. The last is the interesting one: it is the row that decides whether
#: an empty answer means "none" or "not looked at".
#:
#: `rdf:type` triples are separate from `from_organism` triples because
#: `typed_as` in `hfq.biocat` scans `rdf:type` specifically -- the kind test
#: is a different relation from the provenance link, and conflating them
#: would make "which kingdom" and "which strain" the same question.
RXN_TRIPLES: List[Tuple[str, str, str]] = [
    # --- the transamination of Q1 ---------------------------------------
    ("RXN:TA-benzylethylamine", "catalysed_by", "ENZ:TA-Cv"),
    ("RXN:TA-benzylethylamine", "catalysed_by", "ENZ:TA-Pf"),
    ("RXN:TA-benzylethylamine", "catalysed_by", "ENZ:TA-Bs"),
    ("RXN:TA-benzylethylamine", "catalysed_by", "ENZ:TA-Sc"),
    ("RXN:TA-benzylethylamine", "catalysed_by", "ENZ:TA-Ax"),
    ("RXN:TA-benzylethylamine", "consumes",     "CHEBI:benzylethylamine"),
    ("RXN:TA-benzylethylamine", "produces",     "CHEBI:acetophenone"),

    # --- each enzyme's organism -----------------------------------------
    ("ENZ:TA-Cv",  "from_organism", "TAX:Cviolaceum"),
    ("ENZ:TA-Pf",  "from_organism", "TAX:Pfluorescens"),
    ("ENZ:TA-Bs",  "from_organism", "TAX:Bsubtilis"),
    ("ENZ:TA-Sc",  "from_organism", "TAX:Acerevisiae"),
    ("ENZ:TA-Ax",  "from_organism", "TAX:Pfluorescens"),
    ("ENZ:MT-X",   "from_organism", "TAX:Bsubtilis"),
    ("ENZ:BVMO-Y", "from_organism", "TAX:Pfluorescens"),
    ("ENZ:PFE",    "from_organism", "TAX:Pfluorescens"),

    # --- kingdom membership, as a kind test -----------------------------
    ("ENZ:TA-Cv",  "rdf:type", "KIND:bacterial-enzyme"),
    ("ENZ:TA-Pf",  "rdf:type", "KIND:bacterial-enzyme"),
    ("ENZ:TA-Bs",  "rdf:type", "KIND:bacterial-enzyme"),
    ("ENZ:TA-Ax",  "rdf:type", "KIND:bacterial-enzyme"),
    ("ENZ:TA-Sc",  "rdf:type", "KIND:eukaryotic-enzyme"),
    ("ENZ:MT-X",   "rdf:type", "KIND:bacterial-enzyme"),
    ("ENZ:BVMO-Y", "rdf:type", "KIND:bacterial-enzyme"),
    ("ENZ:PFE",    "rdf:type", "KIND:bacterial-enzyme"),

    # --- methyl transfer (Q2) -------------------------------------------
    ("RXN:MT-catechol", "catalysed_by", "ENZ:MT-X"),
    ("RXN:MT-catechol", "consumes",     "CHEBI:catechol"),
    ("RXN:MT-catechol", "consumes",     "CHEBI:SAM"),
    ("RXN:MT-catechol", "produces",     "CHEBI:guaiacol"),

    # --- Baeyer-Villiger (Q3): TWO substrates only ----------------------
    # The scope question asks for the substrate *range* of BVMO-Y. The store
    # holds the two reactions someone ran. It does not hold, and cannot hold,
    # the range -- that is the admissibility point of Q3, and no amount of
    # reasoning over these triples produces a third substrate.
    ("RXN:BV-cyclohexanone", "catalysed_by", "ENZ:BVMO-Y"),
    ("RXN:BV-cyclohexanone", "consumes",     "CHEBI:cyclohexanone"),
    ("RXN:BV-cyclohexanone", "produces",     "CHEBI:caprolactone"),
    ("RXN:BV-2-methylcyclohexanone", "catalysed_by", "ENZ:BVMO-Y"),
    ("RXN:BV-2-methylcyclohexanone", "consumes", "CHEBI:2-methylcyclohexanone"),
    ("RXN:BV-2-methylcyclohexanone", "produces", "CHEBI:7-methyl-caprolactone"),

    # --- kinetic resolution (Q4) ----------------------------------------
    # PFE has been run at pH 7 in phosphate. Q4 asks about pH 9 in HEPES.
    # Nothing here answers that, and the plan must not pretend otherwise.
    ("RXN:KR-phenylethanol", "catalysed_by", "ENZ:PFE"),
    ("RXN:KR-phenylethanol", "consumes",     "CHEBI:rac-1-phenylethanol"),
    ("RXN:KR-phenylethanol", "produces",     "CHEBI:R-1-phenylethyl-acetate"),
    ("RXN:KR-phenylethanol", "produces",     "CHEBI:S-1-phenylethanol"),
]

RXN_PATHS = {
    "reactions_consuming":  "consumes",
    "reactions_producing":  "produces",
    "enzyme_of":            "catalysed_by",
    "participants_of":      "consumes",
    # The inverse family. Each names the edge it walks BACKWARDS: given a
    # compound, which reactions produce it; given an organism, which enzymes
    # come from it. The path is the same stored edge as the forward
    # predicate -- `producers_of` and `reactions_producing` both resolve
    # `produces` -- and only the direction of extraction differs. Keeping
    # them as separate predicate names rather than a direction flag means the
    # capability check sees `path` in Req for the inverse and not for the
    # forward, which is the distinction that lets a one-directionally indexed
    # deployment be refused rather than silently returning nothing.
    "producers_of":         "produces",
    "consumers_of":         "consumes",
    "enzymes_from":         "from_organism",
    "catalysed_reactions":  "catalysed_by",
    "identified_as":        "catalysed_by",
    "matching":             "catalysed_by",
    "excluding":            "catalysed_by",
    "restricted":           "catalysed_by",
    "ranked_by":            "catalysed_by",
    "count_of":             "catalysed_by",
}


# ---------------------------------------------------------------------------
# SEQ -- protein sequences
# ---------------------------------------------------------------------------

#: Four of the five transaminases. TA-Ax is absent: the accession exists in
#: RXN and resolves to no sequence here. That single omission is what makes
#: the `_uncovered` count on every scan row load-bearing rather than
#: decorative.
#:
#: Cysteine (C) is present in TA-Pf and TA-Sc, absent from TA-Cv and TA-Bs.
#: Check by eye -- that is the point of a fixture this size.
SEQUENCES: Dict[str, str] = {
    "ENZ:TA-Cv":  "MQKQRTTSQWRELDAAHHLHPFTDTASLNQAGARVMTRGEGVYLWDSEGNKIIDGMAGLWNVNVGYGRKD",
    "ENZ:TA-Pf":  "MNQPQSWEARAETYSLYGFTDMPSLHQRGTVVVTHGEGCYLYDDQGKAYLDAVGGMWCVNVGYGRKE",
    "ENZ:TA-Bs":  "MSNQELMQRRSQTIPRGVGQIHPIFADRAENARLWDVEGREYIDFAGGIAVLNTGHLHPKVVAAVQ",
    "ENZ:TA-Sc":  "MTLPESKDFSYDAPKTLADFCQQYVMHNSPSKMNLGVGAYRDDNGKPYVLPCVREAEKRLANKQLD",
    "ENZ:MT-X":   "MASMTGGQQMGRDLYDDDKDPMKAVLDLIAGGATSPGGEALLRELAKRHAQVLVIGDDNRSLAWLG",
    "ENZ:BVMO-Y": "MTAQISPTQTTSDVDVLVVGAGFSGLYALYRLRELGRSVHVIETAGDVGGVWYWNRYPGARSDIESIE",
    "ENZ:PFE":    "MSTFVAKNGIRLHYVQEGSGPPLVLLHGFPQTHVMWHRVAPKLAERFTVIAADLRGYGDSSKPEQVED",
    # ENZ:TA-Ax: no entry. Deliberate.
}


# ---------------------------------------------------------------------------
# PROV -- who ran what, when, on which device
# ---------------------------------------------------------------------------

#: Q2's buffer and pH, and Q5's operator/date/device/wavelength, all live
#: here. They are provenance of an *activity*, not properties of a reaction:
#: the same reaction run twice has two buffers, and asking "which buffer was
#: used" without naming the activity is not a well-posed question. That is
#: why these are triples with an activity subject, and it is why Q2's answer
#: is a set rather than a value.
PROV_TRIPLES: List[Tuple[str, str, str]] = [
    ("ACT:BT1", "evaluated",     "RXN:MT-catechol"),
    ("ACT:BT1", "buffer",        "BUF:TrisHCl-50mM"),
    ("ACT:BT1", "pH",            "7.5"),
    ("ACT:BT1", "operator",      "PERSON:YDikova"),
    ("ACT:BT1", "date",          "2026-02-11"),

    ("ACT:BT2", "evaluated",     "RXN:MT-catechol"),
    ("ACT:BT2", "buffer",        "BUF:phosphate-100mM"),
    ("ACT:BT2", "pH",            "8.0"),
    ("ACT:BT2", "operator",      "PERSON:MDoerr"),
    ("ACT:BT2", "date",          "2026-02-18"),

    ("ACT:BT3", "evaluated",     "RXN:KR-phenylethanol"),
    ("ACT:BT3", "buffer",        "BUF:phosphate-50mM"),
    ("ACT:BT3", "pH",            "7.0"),
    ("ACT:BT3", "operator",      "PERSON:YDikova"),
    ("ACT:BT3", "date",          "2026-03-23"),
    ("ACT:BT3", "measured_with", "DEV:UV1900i"),
    ("ACT:BT3", "wavelength",    "254"),

    ("ACT:BT4", "evaluated",     "RXN:BV-cyclohexanone"),
    ("ACT:BT4", "operator",      "PERSON:MDoerr"),
    ("ACT:BT4", "date",          "2026-03-23"),
    ("ACT:BT4", "measured_with", "DEV:Bruker-Avance-400"),
]

PROV_PATHS = {
    "measured_with":       "measured_with",
    "evaluations_of":      "evaluated",
    # PROV holds `measured_with` pointing activity --> device. Q5 asks the
    # forward direction (which device did BT3 use), but the generic
    # Chem-DCAT-AP queries ask the inverse (which datasets were measured on a
    # Bruker), so the edge must be walkable both ways and each direction must
    # declare what it costs.
    "measured_on":         "measured_with",
    "settings_of":         "evaluated",
    "participants_of":     "evaluated",
    "reactions_consuming": "evaluated",
    "enzyme_of":           "evaluated",
    "restricted":          "evaluated",
    "ranked_by":           "evaluated",
    "matching":            "evaluated",
    "excluding":           "evaluated",
    "count_of":            "evaluated",
}


# ---------------------------------------------------------------------------
# INST -- instrument records
# ---------------------------------------------------------------------------

#: A flat REST stand-in. `lookup` and `link` only: no `pattern`. Asking it
#: "which devices are Bruker spectrometers" is a scan it cannot perform, and
#: thm:static refuses such a plan before contact rather than after.
INSTRUMENTS = {
    "DEV:UV1900i": {
        "manufacturer": "Shimadzu", "model": "UV-1900i",
        "kind": "uv-vis-spectrophotometer", "serial": "A12345",
    },
    "DEV:Bruker-Avance-400": {
        "manufacturer": "Bruker", "model": "Avance III 400",
        "kind": "nmr-spectrometer", "serial": "B67890",
    },
}

INST_LINKS = {
    "calibration": {
        "DEV:UV1900i":           ["CAL:2026-01-08"],
        "DEV:Bruker-Avance-400": ["CAL:2026-02-02"],
    }
}


# ---------------------------------------------------------------------------
# Translation: the reaction store's accessions to the sequence store's keys
# ---------------------------------------------------------------------------

#: Partial by construction. Five transaminases in RXN, four with a sequence.
#: On that set retention is 4/5 and the fifth is neither included nor
#: excluded by a residue scan -- it is uncovered, a third outcome the one-bit
#: SPARQL answer has no room for (cor:onebit).
ENZ_SEQ = TranslationMap(
    "enz_to_seq", "RXN", "SEQ",
    {k: (k,) for k in SEQUENCES},
)


def build_biocat_registry() -> Tuple[Registry, MapAdapter]:
    """The five sources, with the capability declarations of def:source.

    Each declaration is a claim by the adapter author about what the
    deployment can be trusted to do. Nothing here verifies any of them
    (rem:honesty-assumption); the comments record the reasoning so that a
    reader can dispute a declaration rather than discover it by surprise.
    """
    reg = Registry()

    # TAX: a subsumption source. `path` and `lookup`, nothing else. It cannot
    # do `neg`: a taxonomy service returns a closure, and "in Bacteria but not
    # in Eukaryota" is set arithmetic the plan performs, not something this
    # source is asked for.
    reg.register(OntologyAdapter(
        name="TAX", namespace="TAX",
        capabilities=featureset("path", "lookup"),
        parents=dict(TAX_PARENTS), labels=dict(TAX_LABELS),
        snapshot=SNAPSHOT))

    # RXN: the reaction store. Note the absence of `agg`. The deployment caps
    # materialisation before aggregating, so a COUNT is well-formed and wrong;
    # prop:under makes withholding the declaration the only honest option, and
    # the effect is that a plan asking for a count is refused by name instead
    # of answered with a plausible number.
    reg.register(FilteringGraphAdapter(
        name="RXN", namespace="RXN",
        capabilities=featureset("pattern", "path", "bind", "filter", "neg",
                                "regex", "order"),
        triples=list(RXN_TRIPLES), paths=dict(RXN_PATHS),
        snapshot=SNAPSHOT))

    # SEQ: sequences by accession. `regex` and `neg` -- it can scan a string
    # it holds -- but NOT `pattern`: it cannot enumerate its own extent, so
    # every scan must be handed its keys by an earlier step.
    reg.register(SequenceAdapter(
        name="SEQ", namespace="SEQ",
        capabilities=featureset("lookup", "regex", "neg", "bind", "batch"),
        sequences=dict(SEQUENCES), snapshot=SNAPSHOT))

    # PROV: activity provenance. A graph source with the same shape as RXN,
    # separately declared because a deployment that publishes reaction data
    # need not publish instrument settings.
    reg.register(ProvenanceAdapter(
        name="PROV", namespace="PROV",
        capabilities=featureset("pattern", "path", "bind", "filter", "neg",
                                "regex", "order"),
        triples=list(PROV_TRIPLES), paths=dict(PROV_PATHS),
        snapshot=SNAPSHOT))

    # INST: the instrument catalogue. `lookup` and `link`; emphatically not
    # `pattern`. "All Bruker spectrometers" is not a question it can answer.
    reg.register(LookupAdapter(
        name="INST", namespace="INST",
        capabilities=featureset("lookup", "link", "bind", "batch"),
        records={k: dict(v) for k, v in INSTRUMENTS.items()},
        links={k: {kk: list(vv) for kk, vv in v.items()}
               for k, v in INST_LINKS.items()},
        snapshot=SNAPSHOT))

    maps = MapAdapter(name="maps", namespace="map", capabilities=frozenset(),
                      maps={"enz_to_seq": ENZ_SEQ})
    maps.snapshot = SNAPSHOT
    return reg, maps
