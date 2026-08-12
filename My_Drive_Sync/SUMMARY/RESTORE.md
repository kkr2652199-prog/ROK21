# RESTORE ??ROK21 ?뺤텞 蹂듭썝 1?쒖쐞 (???뚯씪 ?섎굹硫?蹂듭썝 ?꾨즺)

<!-- ROK21_RESUME_BLOCK -->
## ?숈깮 蹂듦? 5以?(?먮룞 쨌 guard_boot? ?숈씪 ?뚯뒪)

1. **HEAD:** `84dfd17` 쨌 WORK=`IDLE`
2. **吏湲?** **?묒궛??* 쨌 L4 紐곗븘二쇨린?먯옣?쎄린 **WIRE_OK** 쨌 NEXT=L4b ??븷?щ’WIRE
3. **?ㅼ쓬1嫄?** K-TIER-ROLE-SLOTS-WIRE ??**?묒궛??*. L4 紐곗븘二쇨린?먯옣 **WIRE_OK**(repack_by_brain??ledger+scatter ?뚮퉬쨌棺=0.5쨌EMA?⑤룆?덊뵾쨌no_peek쨌1236怨꾩빟45/6). ?ㅼ쓬=**L4b** ??븷?щ’ **WIRE**(skill5+cover_r3횞3+shape_r2횞2 쨌 no_bonus_peek 쨌 prefer/prize 寃뚯씠??. **1237?꾨떂** 쨌 媛뺤젣BT蹂대쪟 쨌 S1 IMMEDIATE??L4??媛쒕퀎?뱀씤. (?뱀씤?꾩슂=?놁쓬(由ъ뒪???쒖꽌쨌??L4 GO ??蹂몄꽑) 쨌 ?좏뻾=L4 WIRE_OK)
4. **SSOT異⑸룎:** ?섏튂=`docs/benchmarks/*.json` 쨌 寃고븿=`FINDINGS.md` 쨌 ?쇰꺼=`WARRANT.md` 媛 ?먮낯. BOOT/STATUS/RESTORE???щ낯.
5. **湲덉??붿빟:** ?숆껐?좏겙쨌kweon誘몄젒珥됀룹빻?앷툑吏쨌DB?꾩껜珥덇린?붽툑吏쨌1~3援곌린濡앷툑吏쨌梨꾪똿媛꾨왂?좊Ц?쒖븬異?

> ?? **?숈깮, EXTERNAL_START.md(?먮뒗 RESTORE) ?쎄퀬 ?쒖옉?? GitHub 404硫??뺤씠 遺숈뿬以 LIVE 釉붾줉留???**
<!-- /ROK21_RESUME_BLOCK -->


> ???몄뀡 ?쒖옉 ??= **"?숈깮, EXTERNAL_START.md ?쎄퀬 ?쒖옉??"** (GitHub 404硫??뺤씠 ?뚯씪 ?꾩껜 遺숈뿬?ｊ린)  
> **?섏튂 SSOT:** `docs/benchmarks/*.json` 쨌 **寃고븿:** `FINDINGS.md` 쨌 **紐낅텇 ?쇰꺼:** `WARRANT.md`  
> BOOT/STATUS/RESTORE/RESUME_HERE ???щ낯 ??異⑸룎 ?????먮낯???닿릿??  
> ?몃?AI 吏꾩엯 1?쒖쐞(猷⑦듃): `EXTERNAL_START.md` 쨌 蹂댁“: `FLOW_BRIEF.md` 쨌 `EXTERNAL_AI_BOOTSTRAP.md`

---

## A) 30珥??붿빟 (5以?

1. **?뺤껜:** ROK21 = ?낅┰ SSOT 쨌 `D:\ROK21` 쨌 ?ы듃 **7021** 쨌 GitHub=`kkr2652199-prog/ROK21`
2. **3????븷:** ??寃곗젙 / ?숈깮(Claude)=?먮떒쨌吏?쒖꽌留?/ 而ㅼ꽌=?ㅽ뻾쨌commit쨌push
3. **?뺤젙 寃곕줎:** ?곸쨷異?**?먭린**. EV 諛곗꽑 ?좎?(Y? ??.033). **K-09 CLOSED**(?ㅼ쭏 ?꾩닔 臾댄빐)쨌?꾩젣?쇰꺼 ?쒓굅
4. **臾쇰━ ?곸닔:** 1??mean=**0.80** 쨌 best-of-15 泥쒖옣=**2.27** (媛쒖꽑 紐⑺몴 ?꾨떂)
5. **?꾩옱 珥덉젏:** **PINNED_BASELINE** `640cb67` 쨌 K-Z~AG ?꾨즺遺?怨좎젙 쨌 ?ㅼ쓬 P1~P4.

---

## B) ??濡쒓렇 (理쒖떊 ??쨌 **理쒕? 12??* 쨌 珥덇낵 ???ㅻ옒??????젣)

| ?쇱떆 | ??吏???붿? | 而ㅼ꽌 ?ㅽ뻾 寃곌낵 | ?먯젙 | 而ㅻ컠 |
|------|--------------|----------------|------|------|
| 2026-08-12 | ?몃??⑥뒪쨌L4b | role 5+3+2 WIRE 쨌 prefer/prize PASS 쨌 NEXT=L5 | **WIRE_OK** | (push?? |
| 2026-08-12 | L4 GO 吏?쒖꽌 | repack ?먯옣?뚮퉬 WIRE 쨌 EMA?덊뵾 쨌 NEXT=L4b | **WIRE_OK** | f7bfe74 |
| 2026-08-12 | ?ㅼ쓬吏꾪뻾 L3 | ledger+scatter WIRE 쨌 1236횞45 쨌 no_peek 쨌 NEXT=L4 | **WIRE_OK** | 05453be |
| 2026-08-12 | L2?먯옣SPEC | ledger+scatter?ㅽ궎留?DOC_OK 쨌 NEXT=L2b | **DOC_OK** | 3131b55 |
| 2026-08-12 | L1?⑸룞smoke | refill??prefer/prize SMOKE_OK 쨌 NEXT=L2 | **SMOKE_OK** | 73e654e |
| 2026-08-12 | ??븷?щ’5+3+2遺꾩꽍 | LIST_V3 DOC 쨌 ?깆닔P?멠ASS 쨌 NEXT=L1 | **DOC_OK** | 7799d81 |
| 2026-08-12 | 由ъ뒪?몃낫媛빧룹썝??~6쨌??0 | LIST_V2 DOC 쨌 NEXT=L1 smoke | **DOC_OK** | 0169137 |
| 2026-08-12 | ?꾪솴+?곸쐞由ъ뒪?맞룐몺??| BT?좊컻沅뙿톓ssue mean1.64쨌??=0 쨌 NEXT??| **METRIC_OK** | 68a5e8d |
| 2026-08-12 | ?ㅼ쓬吏꾪뻾 | ?챉ERIFY_OK쨌?첕Tv5 REBUILT쨌refill_v2 s1/m1/r3 | **DONE** | 594cb9f |
| 2026-08-12 | ?ㅼ쓬吏꾪뻾 | ?쮁MOKE_OK쨌?쯏-C STALE_CLOSE | **DONE** | bb9ff4a |
| 2026-08-12 | ?ㅼ쓬吏꾪뻾쨌quota | min_each1쨌m3/r1/s1 APPLY_OK | **APPLY** | b291681 |
| 2026-08-12 | ?ㅼ쓬?④퀎吏꾪뻾 | K-I WIRE_OK쨌post-refill SMOKE_OK | **DONE** | 7e09f74 |

---

## C) ?뺤젙 ?ъ떎 (?ㅼ쭛?쇰젮硫????ㅼ륫 쨌 ?щ끉??湲덉?)

| ?ъ떎 | ?섏튂 | 洹쇨굅?뚯씪 | 理쒖쥌?뺤씤 而ㅻ컠?댁떆 |
|------|------|----------|------------------|
| 鍮덈룄 ?짼 p (main/bonus) | 0.965 / 0.877 | `docs/benchmarks/20260726_?쒕뜡?깃???` | 誘명솗??|
| OOS ?곸쐞6 mean (freq/markov/recency) | 0.748 / 0.769 / 0.752 | ?숈긽 step2 | 誘명솗??|
| OOS CI?섑븳 > 0.80 | **?놁쓬** ???곸쨷?숈뒿異??먭린 | K-11 쨌 ?쒕뜡?깃???蹂닿퀬??| 誘명솗??|
| ?멸린??Ridge Spearman / ?섎졊諛곗쑉 | 0.440 / 1.180횞 | ?숈긽 step3 | 誘명솗??|
| all3 mean (理쒓렐100) | 0.797 CI[0.75, 0.845] | ?뚭컧??audit | 誘명솗??|
| 1??E[?곸쨷] | **0.80** | 珥덇린??쨌 K-O | `93218f8` |
| AC ?대줎 理쒕퉰 / ???대줎?됯퇏 | **8** / **138** | `docs/benchmarks/20260727_KZ_theory_constants.json` | `3791727` |
| pattern/balance 紐낅텇 | **?ㅼ쬆** | `WARRANT.md` 쨌 K-AA | `bb3fa91` |
| DEDUP E[k] (ON) | **100.000** | `docs/benchmarks/20260727_KV_dedup_verify.json` | `ba98f34` |
| DB MAX lotto4 / testlotto / hyodo | **1234 / 1234 / 1234** | `docs/benchmarks/20260727_KAB_draw_gap.json` 쨌 DB?ㅼ륫 | `e1a7cd2` |

---

## D) ?덈? 湲덉? (7以?

1. `random.choices` **?쇱씤 ?섏젙** 湲덉? (oversample ???좊퀎? ?덉슜)
2. `_get_draws_before` 蹂寃?湲덉?
3. boost ?곹븳 蹂寃?湲덉? (carry 0.2 / ending 0.3 / overdue 0.2)
4. 諛깊뀒 而⑤떇 湲덉? (target ?댄썑 draws쨌?쇰뱶諛??ъ슜)
5. ?먮낯 kweon(`D:\3kweon`)쨌memoy ?곌린 湲덉?
6. DB ?꾩껜珥덇린??鍮꾧텒怨졖룰툑吏??以??
7. STATUS쨌BOOT 蹂몃Ц쨌reports **?뺤텞 湲덉?** (梨꾪똿 ?뚭컙?듐띿? 梨꾪똿留?

---

## E) ?대┛ 寃고븿 (FINDINGS.md ?먮낯 쨌 ?ш린 ?щ낯)

**OPEN (23):** K-00 쨌 K-02 쨌 K-05 쨌 K-08 쨌 K-10 쨌 K-11 쨌 K-12 쨌 K-A 쨌 K-C 쨌 K-E 쨌 K-F 쨌 K-G 쨌 K-I 쨌 K-J 쨌 K-K 쨌 K-L 쨌 K-O 쨌 K-P 쨌 K-Q 쨌 K-R 쨌 K-T 쨌 K-U 쨌 **K-Y(?대젰)**  

**HOLD (2):** K-M 쨌 K-N  

**PATCHED (李멸퀬):** K-06 쨌 K-07 쨌 K-S 쨌 K-V 쨌 K-Z 쨌 K-AA 쨌 K-AB 쨌 K-AC 쨌 K-AD 쨌 K-AE 쨌 K-AF 쨌 **K-AG** 쨌 **K-X** 쨌 **K-W** 쨌 **K-B** 쨌 **K-H** 쨌 **K-D** 쨌 **K-P3** 쨌 **K-P5**  

**CLOSED:** K-01 쨌 K-03 쨌 K-04 쨌 K-09  

??**K-07 = PATCHED** (OPEN ?꾨떂). ?곸꽭쨌鍮꾧퀬??`FINDINGS.md`留??섏젙.

---

## F) ???쎌쓣 ?뚯씪 ?곗꽑?쒖쐞

1. `BOOT.md`
2. `STATUS_LATEST.md`
3. `FINDINGS.md`
4. `WARRANT.md` (紐낅텇 ?쇰꺼)
5. 理쒖떊 `reports/YYYYMMDD_*.md` (?? `20260727_KAB_?뚯감媛?젙??md` 쨌 `20260727_KAC_*.md`)  
   ??援??⑤룆?⑦꽩 `YYYYMMDD_ROK21` ?묐몢?????댁긽 沅뚯옣?섏? ?딆쓬.
