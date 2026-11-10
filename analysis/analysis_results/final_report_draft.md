# Wikipedia Digital Archaeology Project — Analysis Report Draft

## Objective and Motivation

This project examines how Wikipedia articles about selected historical events evolve in the collected revision record. It asks when editing activity changes, how article size changes, how contributor activity is distributed, and whether editing patterns differ across event categories. Revision counts and byte sizes are observable traces of editorial activity; on their own, they do not establish the accuracy, completeness, or historical importance of the resulting content.

## Data and Data Collection

The analysis uses `historical_analysis/cleaned/historical_revisions_cleaned.csv`, a cleaned metadata file with 313,269 revision records and 31 articles. Valid timestamps span 2001-05-14 08:28:10+00:00 to 2026-11-10 06:27:03+00:00, approximately 25.5 years. The data includes article title, revision and parent IDs, timestamp, username and user ID, edit summary, article size, and a minor-edit flag. It does not include the full text of each revision. The project collection scripts and sampling settings should be checked before describing this file as a complete revision history.

The average article has 10,105.5 collected records and the median has 9,034. The largest record counts are concentrated in a few pages:

| article_title | revisions | share_of_records_pct |
| --- | --- | --- |
| World War II | 28609 | 9.132406972921036 |
| September 11 attacks | 22585 | 7.209458963382907 |
| World War I | 20277 | 6.472711950432376 |
| Vietnam War | 19378 | 6.185738135595925 |
| Assassination of John F. Kennedy | 15182 | 4.846314190041147 |
| American Civil War | 14930 | 4.765872141833376 |

The five largest pages by record count contribute 33.8% of the dataset. This uneven coverage matters when interpreting pooled activity: totals reflect both article attention and the choice of articles in the project.

## Data Processing and Quality

Timestamps were parsed as UTC, identifiers and sizes coerced to numeric values, blank usernames treated as unavailable, and records sorted by article, timestamp, and revision ID before calculating consecutive observed size changes. No duplicate revision IDs, missing revision IDs, missing timestamps, negative sizes, or out-of-order input rows were found in the validation pass. Edit summaries were blank for 59,128 records (18.9%). Other required fields in the table below had no missing values.

Parent-link checks found 23 parent IDs absent from the collected dataset and 84 records whose parent timestamp is equal to or later than the child timestamp. These rows are preserved in `step01_parent_link_anomalies.csv` for inspection. Some absent parents may reflect collection boundaries, but the non-earlier timestamps warrant checking against the source history before making fine-grained temporal claims. The largest observed article sizes are also exported because a small number exceed 1 MB; size-based outliers were not silently removed.

## Methods

Monthly and annual revision counts were calculated by article and across the full collection. Monthly spike screening used an article-specific robust threshold: median plus three scaled median absolute deviations. Where the median absolute deviation is zero, the analysis falls back to the upper Tukey fence; when both measures indicate no variation, it flags no observations. This avoids labeling every above-median count as anomalous in sparse series. The resulting table is a screening tool, not a causal explanation.

Article growth compares the first and last observed sizes in the collected record. It reports absolute byte change and percentage change. Percentage change is especially sensitive when the first observed size is very small, so absolute change is presented alongside it. These are observed endpoints, not necessarily page creation and current size. Contributor type is proxied by user ID: zero is classified anonymous, positive values registered, and missing values unavailable. Top-contributor shares are based on usernames within each article; a username does not establish a person's identity. One primary historical-event category was assigned to each article and documented in `step06_article_category_mapping.csv`.

## Results

### Activity and editing spikes

The highest record count belongs to World War II (28,609), followed by September 11 attacks (22,585). That distinction is descriptive and does not mean these events are historically more important. The per-article month table identifies the following large candidate spikes:

| article_title | timestamp | revisions | article_median | robust_threshold |
| --- | --- | --- | --- | --- |
| Arab Spring | 2011-02-01 00:00:00+00:00 | 2050 | 16.0 | 60.478 |
| World War II | 2006-04-01 00:00:00+00:00 | 1588 | 40.0 | 128.95600000000002 |
| World War II | 2006-03-01 00:00:00+00:00 | 1333 | 40.0 | 128.95600000000002 |
| Arab Spring | 2011-03-01 00:00:00+00:00 | 1046 | 16.0 | 60.478 |
| World War II | 2006-09-01 00:00:00+00:00 | 1022 | 40.0 | 128.95600000000002 |
| September 11 attacks | 2006-09-01 00:00:00+00:00 | 865 | 35.0 | 128.4038 |
| World War II | 2006-08-01 00:00:00+00:00 | 849 | 40.0 | 128.95600000000002 |
| World War II | 2006-02-01 00:00:00+00:00 | 848 | 40.0 | 128.95600000000002 |

The Arab Spring page has a 2,050-record month in February 2011 against a per-month median of 16. An external 2011 timeline documents major contemporaneous Arab Spring developments, including Egypt's February transition. For Arab Spring in 2011-02, an external historical timeline documents contemporaneous events. This supports temporal context only and does not show those events caused editing activity. Source: [EU Institute for Security Studies, Timeline 2011](https://www.iss.europa.eu/sites/default/files/3.1__Timeline_2011.pdf). Other spikes remain uninvestigated; the revision counts alone cannot identify anniversaries, media coverage, controversies, or other causes.

The record spans over 25 years, but the files do not provide article publication dates or an independently verified complete history for each page. Therefore, comparisons of first and last observed activity cannot determine whether interest peaks soon after an event or page publication. Further work should establish article creation dates and confirm collection coverage before making that comparison.

### Article size and growth

The largest net observed size increase is September 11 attacks: 323,030 bytes, from 4,849 to 327,879 bytes. The next largest observed increases are summarized here:

| article_title | first_size_bytes | last_size_bytes | net_change_bytes | growth_pct |
| --- | --- | --- | --- | --- |
| September 11 attacks | 4849 | 327879 | 323030.0 | 6661.78593524438 |
| Arab Spring | 822 | 303746 | 302924.0 | 36852.06812652068 |
| Cold War | 30 | 296363 | 296333.0 | 987776.6666666666 |
| Korean War | 109 | 288578 | 288469.0 | 264650.45871559635 |
| Vietnam War | 11303 | 282986 | 271683.0 | 2403.636202778024 |
| Gulf War | 2217 | 262709 | 260492.0 | 11749.751917004962 |

Percentage gains for pages whose earliest collected size was only a few dozen or a few hundred bytes become extremely large. Those percentages should not be compared as if they measured substantive historical knowledge. The largest consecutive size changes in Step 3 include extreme values; their revision IDs are preserved in the candidate table, but a byte delta cannot say what material was added or removed.

### Contributor participation

Across all records, 70.9% have a positive user ID, 29.1% have user ID zero, and the small remainder have unavailable IDs. The median share of revisions attributed to the ten most frequent usernames is 17.4% across articles. This indicates a spread of contribution counts in aggregate, but it cannot identify who contributors are or why they edit. The cleaned `is_minor` column is `True` for all 313,269 rows; consequently every article's minor-edit percentage is 100%. This field has no variation and is not useful for comparing editing behavior until its provenance is verified.

### Event-category comparison

The category analysis compares medians and article counts because the category sizes range from two to ten articles and the article-level distributions are skewed. It is descriptive: category definitions are researcher-assigned, overlapping interpretations are possible, and several category medians are based on very small samples.

| primary_category | articles | median_revisions_per_article | median_revisions_per_year | median_growth_pct |
| --- | --- | --- | --- | --- |
| Revolutions and independence movements | 10 | 5444.0 | 222.49301778809053 | 12528.87815340702 |
| Wars and military conflicts | 8 | 14839.5 | 590.2264896391374 | 8282.6190070107 |
| Natural and technological disasters | 5 | 9565.0 | 427.2103587969647 | 6661.78593524438 |
| Other historical developments | 3 | 9034.0 | 364.7182342663444 | 8891.898042785617 |
| Political events and scandals | 3 | 11365.0 | 453.5828133014389 | 15850.234192037473 |
| Social movements and civil rights | 2 | 6321.5 | 254.408581165634 | 9416.59793376879 |

All categories also show a 100% median minor-edit rate because the input flag is constant. That apparent similarity is a data limitation rather than evidence that editing behavior is the same across event types.

### Significant revision events and content changes

Step 5 retrieved 8 of 8 selected parent/revision comparisons. Inspection confirms several non-substantive events. The Russian Revolution and World War I examples include large vandalism-like text insertions; the World War I page then shows one verified revert, a repeat insertion, and a second verified revert. The JFK and World War II examples also contain nonsensical or repetitive text. By contrast, the recent Vietnam War change adds maintenance templates, the Emancipation Proclamation example adds a bibliography entry, and the American Civil War example removes one casualty-list item. These diffs document edits, not the truth of the affected historical claims. Each row below preserves the revision IDs and a direct diff link for verification.

| article_title | timestamp | revision_id | change_classification |
| --- | --- | --- | --- |
| Russian Revolution | 2005-10-25 19:23:47+00:00 | 26464652 | Vandalism/spam-like text removed |
| World War I | 2005-12-08 13:02:16+00:00 | 30587516 | Vandalism/spam-like text added; not historical content |
| Assassination of John F. Kennedy | 2007-02-19 21:05:08+00:00 | 109385280 | Vandalism/spam-like text removed |
| World War II | 2005-12-23 03:19:58+00:00 | 32441095 | Vandalism/spam-like text added; not historical content |
| September 11 attacks | 2026-11-08 04:05:24+00:00 | 1384420834 | Text or list changed; interpretation requires line-by-line review |
| Vietnam War | 2026-11-06 21:54:36+00:00 | 1384155769 | Maintenance-template addition; flags coverage/length, does not add historical prose |
| Emancipation Proclamation | 2026-11-10 06:27:03+00:00 | 1384830413 | Reference or bibliography addition; source quality needs review |
| American Civil War | 2026-11-09 17:51:56+00:00 | 1384701279 | Text removed; factual reason requires source verification |
| World War I | 2005-12-08 13:02:52+00:00 | 30587560 | Reversion candidate; paired diff removes/changes prior content |
| World War I | 2005-12-08 13:03:19+00:00 | 30587586 | Vandalism/spam-like text added; not historical content |
| World War I | 2005-12-08 13:03:25+00:00 | 30587594 | Verified reversion removing spam-like text |

The World War I sequence is especially informative as an editorial process example: revision 30587516 adds a large profane text block; revision 30587560 removes it about 36 seconds later; revision 30587586 adds it again about 27 seconds after that. Revision 30587594 has a revert edit summary and matching negative size change, but its diff still needs retrieval to verify the exact removal. The verified revisions document a vandalism/reversion cycle in the page history, not a change to historical documentation. See the associated links in `step05_revision_case_studies.csv`.

## Answers to the Research Questions

1. **How does coverage evolve?** The collected records show activity across a long period and substantial differences in record counts and observed page sizes. Completeness and page-creation dates are not established, so these results describe the dataset rather than all Wikipedia history.
2. **When do substantial changes occur?** Robust monthly outliers and large byte deltas identify candidate periods and revisions. They require diff inspection and independent contextual research before interpretation.
3. **Do spikes coincide with public attention?** One Arab Spring example is contemporaneous with independently documented 2011 events. No causal relationship is established; most candidate spikes still need investigation.
4. **What changes are made to historical information?** The retrieved sample includes references, maintenance templates, a list-item removal, and several vandalism/reversion events. The sample is too small to characterize all content changes or assess the historical claims themselves.
5. **Do patterns differ by event type?** The category table shows descriptive differences in medians, but small and uneven category samples, researcher-defined labels, and extreme articles limit generalization.

## Problems, Limitations, and Interpretation

The most important limitation is that this dataset is revision metadata, not the article text or full diff history. Revision count is not a direct measure of public attention, accuracy, quality, or historical importance. Size changes include references, markup, templates, and formatting. Parent-link anomalies and large size outliers need source-level validation. Contributor metadata supports only aggregate classifications. The constant minor-edit field should be traced to the cleaning or collection process. Category comparisons may change under a different mapping, and category groups contain few pages. External context is incomplete and should be linked to dated independent sources.

## Future Work

First, run the Step 5 retrieval cell where the Wikimedia API is reachable and document a small set of verified diffs across multiple articles. Second, audit the 84 non-earlier parent links, 23 parent IDs absent from the collected file, and large page-size outliers. Third, verify whether the collected revision record is complete or sampled and obtain page creation dates. Fourth, investigate the largest monthly spikes with dated external sources while separating coincidence from cause. Fifth, confirm why `is_minor` is constant and correct the source data if necessary. These actions would make a report about content evolution stronger than one based solely on activity counts.

## Team Contributions

[Add team members and verified contributions. This information was not present in the project files available for this analysis.]

## Repository

[Insert the final repository link.]
