# Disagreement exhibits -- lenient judge says CORRECT, strict says WRONG (863 unique cases, full run)

Same Mem0 answer, same gold. Only the grading prompt differs. Full set in
`disagreement_exhibits.json`; 25 illustrative cases below.

## 1. [temporal] conv0 qconv0_q0
- **Q:** When did Caroline go to the LGBTQ support group?
- **Gold:** 7 May 2023
- **Answer:** - May 7, 2023
- June 26, 2023
- **mem0 judge (CORRECT):** The generated answer includes May 7, 2023, which matches the gold date of 7 May 2023.
- **strict judge (WRONG):** The generated answer adds an extra date (June 26, 2023) not in the gold answer, so it does not exactly match the required single date of 7 May 2023.

## 2. [temporal] conv0 qconv0_q10
- **Q:** How long has Caroline had her current group of friends for?
- **Gold:** 4 years
- **Answer:** Four years (since she moved from her home country around June 2019).
- **mem0 judge (CORRECT):** The generated answer states 'Four years,' which matches the gold answer exactly.
- **strict judge (WRONG):** While it gives 'Four years,' it adds unverified specifics about moving in June 2019, which violates the no-fabrication rule.

## 3. [single-hop] conv0 qconv0_q100
- **Q:** What kind of place does Caroline want to create for people?
- **Gold:** a safe and inviting place for people to grow
- **Answer:** A safe, inviting place where people can grow (a supportive environment she aims to foster through her counseling work).
- **mem0 judge (CORRECT):** The generated answer restates the gold answer’s idea of a safe, inviting place for people to grow.
- **strict judge (WRONG):** Although it matches the phrase 'safe and inviting place for people to grow,' it adds an unverified detail about doing so through her counseling work, which goes beyond the gold answer.

## 4. [single-hop] conv0 qconv0_q101
- **Q:** Did Melanie make the black and white bowl in the photo?
- **Gold:** Yes
- **Answer:** Yes. Melanie made the black‑and‑white bowl herself in her pottery class.
- **mem0 judge (CORRECT):** The generated answer matches the gold by stating that Melanie made the black-and-white bowl, capturing the same core fact.
- **strict judge (WRONG):** Although it answers Yes, it adds an unverified detail ('in her pottery class'), violating the no-fabricated-specifics rule.

## 5. [single-hop] conv0 qconv0_q104
- **Q:** What book did Caroline recommend to Melanie?
- **Gold:** "Becoming Nicole"
- **Answer:** Becoming Nicole by Amy Ellis Nutt
- **mem0 judge (CORRECT):** The generated answer correctly names the book 'Becoming Nicole,' and adding the author is acceptable extra detail.
- **strict judge (WRONG):** The generated answer adds an extra specific (the author) beyond the gold answer, which must match exactly under the strict criteria.

## 6. [single-hop] conv0 qconv0_q105
- **Q:** What did Caroline take away from the book "Becoming Nicole"?
- **Gold:** Lessons on self-acceptance and finding support
- **Answer:** She found it an inspiring true story of a trans girl and her family that made her feel connected and gave her hope for her own path.
- **mem0 judge (CORRECT):** The generated answer emphasizes feeling connected (support) and gaining hope for her own path (self-acceptance), aligning with the gold takeaways.
- **strict judge (WRONG):** The generated answer mentions inspiration, connection, and hope but does not state the lessons of self-acceptance and finding support specified in the gold answer.

## 7. [single-hop] conv0 qconv0_q107
- **Q:** What is Melanie's reason for getting into running?
- **Gold:** To de-stress and clear her mind
- **Answer:** To de-stress and clear her mind—running helps her headspace and gives her me-time so she can stay present for her family.
- **mem0 judge (CORRECT):** The generated answer states she runs to de-stress and clear her mind, matching the gold answer exactly.
- **strict judge (WRONG):** Although it matches 'to de-stress and clear her mind,' it adds unverified specifics about headspace, me-time, and family presence, which violates the strict criteria.

## 8. [single-hop] conv0 qconv0_q108
- **Q:** What does Melanie say running has been great for?
- **Gold:** Her mental health
- **Answer:** Her headspace.
- **mem0 judge (CORRECT):** “Headspace” is a clear paraphrase of “mental health,” referring to the same concept.
- **strict judge (WRONG):** The generated answer says “Her headspace,” which is a vague paraphrase and does not exactly match the gold answer “Her mental health.”

## 9. [single-hop] conv0 qconv0_q109
- **Q:** What did Mel and her kids make during the pottery workshop?
- **Gold:** pots
- **Answer:** They each made their own pots—one was a cup featuring a dog face.
- **mem0 judge (CORRECT):** The generated answer explicitly states they made pots, matching the gold answer.
- **strict judge (WRONG):** Although it mentions pots, it adds an unverified detail about a cup with a dog face, which is not in the gold answer and violates the no-fabricated-specifics rule.

## 10. [single-hop] conv0 qconv0_q111
- **Q:** What creative project do Mel and her kids do together besides pottery?
- **Gold:** painting
- **Answer:** Painting together—nature‑inspired pieces like a vibrant sunset with a palm tree.
- **mem0 judge (CORRECT):** The generated answer mentions painting together, which matches the gold answer exactly.
- **strict judge (WRONG):** Although it correctly says painting, it adds unverified specifics about nature-inspired pieces and a sunset with a palm tree, which violates the no-fabrication rule.

## 11. [single-hop] conv0 qconv0_q113
- **Q:** What did Caroline see at the council meeting for adoption?
- **Gold:** many people wanting to create loving homes for children in need
- **Answer:** Many participants who wanted to create loving homes for children.
- **mem0 judge (CORRECT):** The generated answer paraphrases the gold response by stating many participants wanted to create loving homes for children, matching the core idea.
- **strict judge (WRONG):** The generated answer omits the qualifier 'in need' from 'children in need,' so it does not fully match the gold facts.

## 12. [single-hop] conv0 qconv0_q115
- **Q:** Why are flowers important to Melanie?
- **Gold:** They remind her to appreciate the small moments and were a part of her wedding decor
- **Answer:** Because they bring her joy, symbolize growth and beauty, and remind her to appreciate small moments—and since they were a key part of her wedding décor, they now always remind her of her wedding day.
- **mem0 judge (CORRECT):** The generated answer includes both gold points: appreciating small moments and their role in her wedding décor, linking them to her wedding day.
- **strict judge (WRONG):** Although it mentions appreciating small moments and wedding decor, it adds unverified details (joy, symbolism, reminding her of her wedding day) and changes “a part” to “a key part,” so it does not strictly match the gold facts.

## 13. [single-hop] conv0 qconv0_q119
- **Q:** How did Melanie feel while watching the meteor shower?
- **Gold:** in awe of the universe
- **Answer:** She felt at one with the universe.
- **mem0 judge (CORRECT):** Feeling “at one with the universe” conveys a similar positive, transcendent sentiment toward the universe as being “in awe,” matching the core idea.
- **strict judge (WRONG):** The generated answer says she felt 'at one with the universe,' which differs from the gold answer's 'in awe of the universe' and does not match the exact feeling required.

## 14. [temporal] conv0 qconv0_q12
- **Q:** How long ago was Caroline's 18th birthday?
- **Gold:** 10 years ago
- **Answer:** Ten years ago (on June 27, 2013).
- **mem0 judge (CORRECT):** The generated answer correctly states that Caroline’s 18th birthday was ten years ago, matching the gold answer, with the added date detail being acceptable.
- **strict judge (WRONG):** Although it matches '10 years ago,' it improperly adds an unverified specific date (June 27, 2013) not in the gold answer.

## 15. [single-hop] conv0 qconv0_q122
- **Q:** Why did Melanie choose to use colors and patterns in her pottery project?
- **Gold:** She wanted to catch the eye and make people smile.
- **Answer:** Because pottery is how she expresses her feelings and finds joy, she chose vivid colors and patterns to be eye‑catching and make people smile, using the design as a form of self‑expression and connection. Many of her motifs (like floral patterns and purple glazes) also reflect her love of nature, which she finds calming and uplifting.
- **mem0 judge (CORRECT):** The generated answer explicitly says she chose vivid colors and patterns to be eye-catching and make people smile, matching the gold answer’s reasons.
- **strict judge (WRONG):** Although it includes 'eye‑catching' and 'make people smile,' it adds unverified details (self‑expression, connection, nature themes, floral patterns, purple glazes), so it does not strictly match the gold facts.

## 16. [single-hop] conv0 qconv0_q123
- **Q:** What pet does Caroline have?
- **Gold:** guinea pig
- **Answer:** A guinea pig named Oscar.
- **mem0 judge (CORRECT):** The generated answer correctly identifies the pet as a guinea pig, matching the gold answer.
- **strict judge (WRONG):** The generated answer adds an unverified specific (‘named Oscar’) beyond the gold fact of just ‘guinea pig,’ so it does not exactly match.

## 17. [single-hop] conv0 qconv0_q124
- **Q:** What pets does Melanie have?
- **Gold:** Two cats and a dog
- **Answer:** Melanie has a dog named Oliver and two cats, Luna and Bailey.
- **mem0 judge (CORRECT):** The generated answer matches the gold answer by stating Melanie has a dog and two cats, with extra pet names being acceptable detail.
- **strict judge (WRONG):** Although the counts match, the generated answer adds unverified pet names not in the gold answer, violating the no-fabrication rule.

## 18. [single-hop] conv0 qconv0_q127
- **Q:** What did Caroline make for a local church?
- **Gold:** a stained glass window
- **Answer:** A large stained glass window depicting time changing lives.
- **mem0 judge (CORRECT):** The generated answer specifies a stained glass window, matching the gold answer even with extra descriptive detail.
- **strict judge (WRONG):** The generated answer adds unverified specifics (“large” and the depiction) not in the gold answer, so it does not exactly match the stated fact.

## 19. [single-hop] conv0 qconv0_q131
- **Q:** Who is Melanie a fan of in terms of modern music?
- **Gold:** Ed Sheeran
- **Answer:** Ed Sheeran (she mentioned enjoying his song “Perfect”).
- **mem0 judge (CORRECT):** The generated answer correctly identifies Ed Sheeran as the modern artist Melanie is a fan of, matching the gold answer.
- **strict judge (WRONG):** Although it correctly names Ed Sheeran, it adds an unverified detail about her enjoying the song “Perfect,” which violates the no extra specifics rule.

## 20. [single-hop] conv0 qconv0_q133
- **Q:** What precautionary sign did Melanie see at the café?
- **Gold:** A sign stating that someone is not being able to leave
- **Answer:** A sign on the door stating that someone was not able to leave (a precautionary notice).
- **mem0 judge (CORRECT):** The generated answer restates the gold answer’s content that the sign said someone was not able to leave, matching the core idea.
- **strict judge (WRONG):** The generated answer adds an unmentioned detail (“on the door”) and alters the phrasing, so it does not exactly match the gold answer’s facts.

## 21. [single-hop] conv0 qconv0_q134
- **Q:** What advice does Caroline give for getting started with adoption?
- **Gold:** Do research, find an adoption agency or lawyer, gather necessary documents, and prepare emotionally.
- **Answer:** Research and choose an adoption agency or lawyer, gather key documents (personal references, financial information, and medical checks), and prepare emotionally for a potentially long wait.
- **mem0 judge (CORRECT):** The generated answer includes all key points from the gold answer: research, selecting an agency/lawyer, gathering documents, and preparing emotionally.
- **strict judge (WRONG):** Although it covers all four points, it adds unverified specifics (types of documents and a long wait) not in the gold answer, which violates the strict match requirement.

## 22. [single-hop] conv0 qconv0_q136
- **Q:** What does Melanie do to keep herself busy during her pottery break?
- **Gold:** Read a book and paint.
- **Answer:** She kept busy by painting and by reading the memoir “Becoming Nicole” by Amy Ellis Nutt.
- **mem0 judge (CORRECT):** The generated answer includes both activities—painting and reading a book—which match the gold answer.
- **strict judge (WRONG):** Although it includes reading and painting, it adds an unverified specific book title and author not in the gold answer, violating the strict criteria.

## 23. [single-hop] conv0 qconv0_q137
- **Q:** What painting did Melanie show to Caroline on October 13, 2023?
- **Gold:** A painting inspired by sunsets with a pink sky.
- **Answer:** A landscape painting of a sunset with a pink sky.
- **mem0 judge (CORRECT):** The generated answer matches the gold by describing a sunset-themed painting with a pink sky, which is a clear paraphrase.
- **strict judge (WRONG):** The generated answer adds unverified detail ('landscape') and changes 'inspired by sunsets' to 'of a sunset,' so it does not exactly match the gold facts.

## 24. [single-hop] conv0 qconv0_q139
- **Q:** What was the poetry reading that Caroline attended about?
- **Gold:** It was a transgender poetry reading where transgender people shared their stories.
- **Answer:** A transgender poetry reading focused on trans people sharing their personal stories and identities through poetry—an empowering, safe‑space event celebrating trans lives.
- **mem0 judge (CORRECT):** The generated answer matches the gold by describing a transgender poetry reading where trans people shared their personal stories, with acceptable extra details.
- **strict judge (WRONG):** Although it matches the core facts (a transgender poetry reading where trans people shared their stories), it adds unverified specifics about being an “empowering, safe-space event celebrating trans lives,” which is not in the gold answer.

## 25. [open-domain] conv0 qconv0_q14
- **Q:** Would Caroline still want to pursue counseling as a career if she hadn't received support growing up?
- **Gold:** Likely no
- **Answer:** Likely no. Caroline links her decision to pursue counseling directly to the support she received—she says that support “made a huge difference,” sparked her passion to create safe, inviting spaces, and showed her how crucial a supportive network is. Without having experienced that support, she probably wouldn’t feel the same motivation (or the same certainty) to choose counseling as her career.
- **mem0 judge (CORRECT):** The generated answer explicitly says 'Likely no,' matching the gold answer's conclusion and providing aligned rationale.
- **strict judge (WRONG):** Although it matches the gold answer’s “Likely no,” it adds unverified specifics and a quote not in the gold, violating the strict no-fabrication rule.
