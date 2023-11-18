# Fact check
Required processes:
- **Media scan**: fast and robust selection process to identify items to be checked
- **Fact check**: multiphase verification protocol

## Media scan
```mermaid
%%{init: {'theme':'neutral'}}%%
stateDiagram
  direction LR
classDef output font-style:italic,fill:#ffffff
%%%
scan_news_media: Scan News
check_sm_trends: Scan Social Media
scan_fact_checkers: Scan Fact Checkers
watch_known_outlets: Scan known outlets
model_topics: Model recent topics
generate_search_terms: Generate search terms
search_social_media: Search Social Media
search_web: Search Web
score_candidates: Score candidates
%%%
[*] --> scan_news_media
[*] --> check_sm_trends
[*] --> scan_fact_checkers
[*] --> watch_known_outlets
check_sm_trends --> model_topics
scan_news_media --> model_topics
scan_fact_checkers --> model_topics
model_topics --> generate_search_terms
generate_search_terms --> search_social_media
generate_search_terms --> search_web
search_social_media --> score_candidates
search_web --> score_candidates
watch_known_outlets --> score_candidates
score_candidates --> [*]
```

## Fact check process 
### Overview

```mermaid
%%{init: {'theme':'neutral'}}%%
stateDiagram
  direction TB
classDef output font-style:italic,fill:#ffffff
%%%
overview: Process overview
%%%
extract_claim: Extract claim
check_worthy: Detect check worthy
context: Contextualize
known: Lookup known claims
evidence: Discover evidence
appearance: Register appearance
%%%
not_check_worthy:::output: Not check worthy
new_verdict_and_evidence:::output: Generated verdict with source citations
known_verdict_and_reference:::output: Known verdict with source citations
unverifiable:::output: No sufficient evidence 
state overview{
  direction LR
    state is_check_worthy <<choice>>
    state is_known <<choice>>
    state is_evidence <<choice>>
    [*] --> extract_claim
    extract_claim --> context
    context --> check_worthy
    check_worthy --> is_check_worthy
    not_check_worthy --> [*]
    is_check_worthy--> known: Yes
    is_check_worthy--> not_check_worthy: No
    known --> is_known
    is_known --> known_verdict_and_reference: Yes
    known_verdict_and_reference --> appearance
    known_verdict_and_reference --> [*]
    is_known --> evidence: No
    evidence --> is_evidence
    is_evidence --> new_verdict_and_evidence: Yes
    is_evidence --> unverifiable: No
    new_verdict_and_evidence --> [*]
    unverifiable --> [*]
    


}
```
### Extract claim
```mermaid
stateDiagram
  direction TB
%%{init: {'theme':'neutral'}}%%
%%%
claim_extract: Extract claim
%%%
claim_text_split: Split text
claim_paraphrase: Formulate claim
claim_augment: Augment claim
claim_control: Check correctness (NLI)
claim_rewrite: Rewrite
%%%
state claim_extract{
  direction LR
  [*] --> claim_text_split
  claim_text_split --> claim_paraphrase
  claim_paraphrase  --> claim_augment
  claim_augment --> claim_control
  state is_claim_correct <<choice>>
  claim_control --> is_claim_correct
  is_claim_correct --> [*]: Yes
  is_claim_correct --> claim_rewrite: No
  claim_rewrite --> claim_control 

  }
```
### Contextualize claim
```mermaid
stateDiagram
  direction TB
%%{init: {'theme':'neutral'}}%%
%%%
claim_contextualize: Contextualize claim
%%%
claim_metadata: Acquire metadata
claim_ner_find: Find Named Entities
claim_ner_disambiguation: Disambiguate NE
claim_context_augmentation: Augment context
%%%
state claim_contextualize {
  direction LR
  [*] --> claim_metadata
  claim_metadata --> claim_ner_find
  claim_ner_find --> claim_ner_disambiguation
  claim_ner_disambiguation --> claim_context_augmentation
  claim_context_augmentation --> [*]
  }
```

### Detect check worthy claims
```mermaid
stateDiagram
  direction TB
%%{init: {'theme':'neutral'}}%%
state fork <<fork>>
state join <<join>>
claim_check_worthy: Detect check worthy claims

has_verifiable_content: Check for verifiable content
is_opinion: Check for personal opinion
rate_expected_harmfulness: Check for harmfulness
rate_expected_reach: Estimate reach
check_for_sensitive_topic: Check for sensitive topic
score_claim: Score claim check worthiness

state claim_check_worthy{
  direction LR
  [*] --> fork
  fork --> has_verifiable_content
  fork --> is_opinion
  fork --> rate_expected_harmfulness
  fork --> rate_expected_reach
  fork --> check_for_sensitive_topic
  has_verifiable_content --> join
  is_opinion --> join
  rate_expected_harmfulness --> join
  rate_expected_reach --> join
  check_for_sensitive_topic --> join
  check_for_sensitive_topic
  join --> score_claim
  score_claim --> [*]
}
```
### Lookup known high-quality sources
```mermaid
stateDiagram
  direction TB
%%{init: {'theme':'neutral'}}%%
%%%
sources_find: Lookup known claims
%%%
generate_embeddings: Make embeddings
lookup_fakes: Lookup known fakes
lookup_trusted: Lookup trusted sources
lookup_rerank: Rerank similar 
match_known_nli: Match with NLI
copy_verdict: Make verdict
state sources_find {
  direction LR
    [*] --> generate_embeddings
    generate_embeddings --> lookup_fakes
    generate_embeddings --> lookup_trusted
    lookup_fakes --> lookup_rerank
    lookup_trusted--> lookup_rerank
    lookup_rerank --> match_known_nli
    match_known_nli --> copy_verdict
    copy_verdict --> [*]
  }
```
### Discover evidence and rate claim
```mermaid
stateDiagram
  direction TB
%%{init: {'theme':'neutral'}}%%
%%% 
evidence_find: Find evidence
%%%
decompose_claim: Decompose claim
search_decomposed: Recursive search for decomposed claim element
generate_search_terms: Generate search terms
search_web: Search Web
extract_source_claims: Extract source claims
match_source_nli: Match sources with NLI
partial_verdict_from_evidence: Determine partial verdict
final_verdict_from_evidence: Determine final verdict
lookup_source_reputation: Lookup source reputation
writeup_debunk: Write-up debunk
%%%
state evidence_find {
  [*] --> decompose_claim 
  decompose_claim --> search_decomposed
  direction LR
    state search_decomposed {
      direction LR

    [*] --> generate_search_terms
    generate_search_terms --> search_web
    search_web --> lookup_source_reputation
    search_web --> extract_source_claims
    extract_source_claims --> match_source_nli
    match_source_nli --> partial_verdict_from_evidence
    lookup_source_reputation --> partial_verdict_from_evidence partial_verdict_from_evidence --> [*]
    }
    search_decomposed --> final_verdict_from_evidence
    final_verdict_from_evidence --> writeup_debunk
  }
```
# Components
- topic classification and modeling:
  - general topics for sensitive topic lists
  - granular topics for narratives definition

- source reputation:
  - per outlet: wiki rank weighted by popularity 
  - per author: for social media only 
- known claims database fact-checkers
- true claims from trusted sources

