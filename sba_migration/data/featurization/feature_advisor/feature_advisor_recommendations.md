# Feature Advisor Recommendations

## asofdate
- Recommended method: Review metadata
- Rationale: The field does not match a recognized categorical, numeric, or text featurization pattern. Validate whether it should be treated as a specialized text or hierarchical categorical field.

## program
- Recommended method: No encoding required
- Rationale: Numeric feature should be passed through the numeric pipeline without additional categorical encoding, preserving train/validation artifact separation.

## locationid
- Recommended method: No encoding required
- Rationale: Numeric feature should be passed through the numeric pipeline without additional categorical encoding, preserving train/validation artifact separation.

## borrname
- Recommended method: TF-IDF + TruncatedSVD
- Rationale: Short text or keyword-style field. Fit sparse TF-IDF on train only and compress with TruncatedSVD to preserve train/validation safety while limiting sparse dimensionality.

## borrstreet
- Recommended method: TF-IDF + TruncatedSVD
- Rationale: Short text or keyword-style field. Fit sparse TF-IDF on train only and compress with TruncatedSVD to preserve train/validation safety while limiting sparse dimensionality.

## borrcity
- Recommended method: TF-IDF + TruncatedSVD
- Rationale: Short text or keyword-style field. Fit sparse TF-IDF on train only and compress with TruncatedSVD to preserve train/validation safety while limiting sparse dimensionality.

## borrstate
- Recommended method: low_count_cat_var_encoding + target_encoding
- Rationale: Use low-count categorical grouping on train data followed by target encoding to produce numeric model-ready features while avoiding unseen categories during validation/active scoring.

## borrzip
- Recommended method: low_count_cat_var_encoding + target_encoding
- Rationale: Use low-count categorical grouping on train data followed by target encoding to produce numeric model-ready features while avoiding unseen categories during validation/active scoring.

## grossapproval
- Recommended method: No encoding required
- Rationale: Numeric feature should be passed through the numeric pipeline without additional categorical encoding, preserving train/validation artifact separation.

## approvaldate
- Recommended method: Review metadata
- Rationale: The field does not match a recognized categorical, numeric, or text featurization pattern. Validate whether it should be treated as a specialized text or hierarchical categorical field.

## approvalfy
- Recommended method: No encoding required
- Rationale: Numeric feature should be passed through the numeric pipeline without additional categorical encoding, preserving train/validation artifact separation.

## firstdisbursementdate
- Recommended method: Review metadata
- Rationale: The field does not match a recognized categorical, numeric, or text featurization pattern. Validate whether it should be treated as a specialized text or hierarchical categorical field.

## processingmethod
- Recommended method: low_count_cat_var_encoding + target_encoding
- Rationale: Use low-count categorical grouping on train data followed by target encoding to produce numeric model-ready features while avoiding unseen categories during validation/active scoring.

## subprogram
- Recommended method: low_count_cat_var_encoding + target_encoding
- Rationale: Use low-count categorical grouping on train data followed by target encoding to produce numeric model-ready features while avoiding unseen categories during validation/active scoring.

## terminmonths
- Recommended method: No encoding required
- Rationale: Numeric feature should be passed through the numeric pipeline without additional categorical encoding, preserving train/validation artifact separation.

## naicscode
- Recommended method: hierarchical_low_count_var_encoding
- Rationale: Hierarchical or geographic long-tail categorical code. Use right-side masking to preserve parent-level industry/geo structure while meeting minimum support on train data.

## naicsdescription
- Recommended method: SentenceTransformer
- Rationale: Long-form or descriptive text field. Use a stateless SentenceTransformer embedder to capture semantic context and avoid leaking validation data through train-only vocabulary fitting.

## franchisecode
- Recommended method: low_count_cat_var_encoding + target_encoding
- Rationale: Use low-count categorical grouping on train data followed by target encoding to produce numeric model-ready features while avoiding unseen categories during validation/active scoring.

## franchisename
- Recommended method: low_count_cat_var_encoding + target_encoding
- Rationale: Use low-count categorical grouping on train data followed by target encoding to produce numeric model-ready features while avoiding unseen categories during validation/active scoring.

## projectcounty
- Recommended method: TF-IDF + TruncatedSVD
- Rationale: Short text or keyword-style field. Fit sparse TF-IDF on train only and compress with TruncatedSVD to preserve train/validation safety while limiting sparse dimensionality.

## projectstate
- Recommended method: low_count_cat_var_encoding + target_encoding
- Rationale: Use low-count categorical grouping on train data followed by target encoding to produce numeric model-ready features while avoiding unseen categories during validation/active scoring.

## sbadistrictoffice
- Recommended method: low_count_cat_var_encoding + target_encoding
- Rationale: Use low-count categorical grouping on train data followed by target encoding to produce numeric model-ready features while avoiding unseen categories during validation/active scoring.

## congressionaldistrict
- Recommended method: low_count_cat_var_encoding + target_encoding
- Rationale: Use low-count categorical grouping on train data followed by target encoding to produce numeric model-ready features while avoiding unseen categories during validation/active scoring.

## businesstype
- Recommended method: low_count_cat_var_encoding + target_encoding
- Rationale: Use low-count categorical grouping on train data followed by target encoding to produce numeric model-ready features while avoiding unseen categories during validation/active scoring.

## businessage
- Recommended method: low_count_cat_var_encoding + target_encoding
- Rationale: Use low-count categorical grouping on train data followed by target encoding to produce numeric model-ready features while avoiding unseen categories during validation/active scoring.

## loanstatus
- Recommended method: low_count_cat_var_encoding + target_encoding
- Rationale: Use low-count categorical grouping on train data followed by target encoding to produce numeric model-ready features while avoiding unseen categories during validation/active scoring.

## paidinfulldate
- Recommended method: Review metadata
- Rationale: The field does not match a recognized categorical, numeric, or text featurization pattern. Validate whether it should be treated as a specialized text or hierarchical categorical field.

## chargeoffdate
- Recommended method: Review metadata
- Rationale: The field does not match a recognized categorical, numeric, or text featurization pattern. Validate whether it should be treated as a specialized text or hierarchical categorical field.

## grosschargeoffamount
- Recommended method: No encoding required
- Rationale: Numeric feature should be passed through the numeric pipeline without additional categorical encoding, preserving train/validation artifact separation.

## jobssupported
- Recommended method: No encoding required
- Rationale: Numeric feature should be passed through the numeric pipeline without additional categorical encoding, preserving train/validation artifact separation.

## collateralind
- Recommended method: No encoding required
- Rationale: Numeric feature should be passed through the numeric pipeline without additional categorical encoding, preserving train/validation artifact separation.
