from app.services.deduplication import (
    CanonicalEntity,
    DeduplicationStatus,
    content_hash,
    deduplicate_document,
    deduplicate_entity,
)


def entity(entity_id: str, name: str, entity_type: str, aliases=None, context=None):
    return CanonicalEntity(
        entity_id=entity_id,
        name=name,
        entity_type=entity_type,
        aliases=aliases or [],
        context=context or [],
    )


def test_exact_duplicate_document_uses_content_hash():
    fingerprint = content_hash(b"same uploaded material")
    result = deduplicate_document(b"same uploaded material", [("doc-1", fingerprint)])
    assert result.status is DeduplicationStatus.DUPLICATE
    assert result.matched_document_id == "doc-1"


def test_memory_market_variants_are_duplicate_candidates():
    existing = entity("project-1", "Memory Market", "project")
    for mention in ["memory-market", "MemoryMarket"]:
        result = deduplicate_entity(entity("mention", mention, "project"), [existing])
        assert result.status in {
            DeduplicationStatus.DUPLICATE,
            DeduplicationStatus.POSSIBLE_DUPLICATE,
        }


def test_rose_person_and_flower_are_not_merged():
    person = entity("person-rose", "Rose", "person", context=["Sarah", "told"])
    flower = entity("flower-rose", "Rose", "flower", context=["garden", "dying"])

    person_result = deduplicate_entity(
        entity("mention-1", "Rose", "person", context=["Sarah", "told"]),
        [person, flower],
    )
    flower_result = deduplicate_entity(
        entity("mention-2", "Rose", "flower", context=["garden", "dying"]),
        [person, flower],
    )

    assert person_result.candidates[0].entity.entity_id == "person-rose"
    assert flower_result.candidates[0].entity.entity_id == "flower-rose"


def test_ambiguous_entity_is_preserved_as_possible_duplicate():
    candidates = [
        entity("a", "Memory Market", "project"),
        entity("b", "Memory Market", "project"),
    ]
    result = deduplicate_entity(entity("mention", "Memory Market", "project"), candidates)
    assert result.status is DeduplicationStatus.POSSIBLE_DUPLICATE
    assert len(result.candidates) == 2
