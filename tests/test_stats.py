from mend.stats import sign_test, token_ratio_ci


def test_sign_test_exact_values():
    assert sign_test(0, 0) == 1.0 and sign_test(1, 1) == 1.0
    assert sign_test(5, 0) == 0.0625 and sign_test(10, 0) == 2 / 1024


def test_token_ratio_ci_brackets_the_ratio():
    pairs = [(100, 70 + i) for i in range(20)]
    ratio, lo, hi = token_ratio_ci(pairs)
    assert lo <= ratio <= hi < 1.0
