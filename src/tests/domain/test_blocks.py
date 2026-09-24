from dcprepa.domain.blocks import PreparedBlock, prepare_block

DECKS = {"terra-midrange": ["v1", "v2"]}
DECK_INDEX = {"terra-midrange": "terra-midrange", "terra": "terra-midrange"}
OPPO_INDEX = {"ragavan": "Ragavan", "raga": "Ragavan"}
BLOCK = {"date": "02/10/2026", "source": "paper", "deck": "Terra", "version": "v1", "oppo": "raga", "games": "OTP W, OTD W / OTD L"}


def test_bloc_valide():
    used_ids = {"02/10/2026-01"}
    prepared = prepare_block(BLOCK, DECKS, DECK_INDEX, OPPO_INDEX, used_ids)
    assert (prepared.matches, prepared.errors, prepared.warnings) == (2, [], [])
    assert [(row["match_id"], row["game"], row["deck"], row["oppo"]) for row in prepared.rows] == [
        ("02/10/2026-02", "1", "terra-midrange", "Ragavan"),
        ("02/10/2026-02", "2", "terra-midrange", "Ragavan"),
        ("02/10/2026-03", "1", "terra-midrange", "Ragavan"),
    ]
    assert used_ids == {"02/10/2026-01", "02/10/2026-02", "02/10/2026-03"}


def test_bloc_invalide_aucune_ligne():
    used_ids = set()
    prepared = prepare_block({**BLOCK, "version": "v9"}, DECKS, DECK_INDEX, OPPO_INDEX, used_ids)
    assert prepared.rows == [] and prepared.matches == 0 and prepared.errors
    assert used_ids == set()


def test_oppo_inconnu_avertissement():
    prepared = prepare_block({**BLOCK, "oppo": "Kess"}, DECKS, DECK_INDEX, OPPO_INDEX, set())
    assert prepared.errors == [] and len(prepared.warnings) == 1
    assert prepared.rows[0]["oppo"] == "Kess"


def test_bloc_qui_n_est_pas_un_dictionnaire():
    prepared = prepare_block("n'importe quoi", DECKS, DECK_INDEX, OPPO_INDEX, set())
    assert isinstance(prepared, PreparedBlock) and prepared.errors and prepared.rows == []
