# -*- coding: utf8 -*-
import hdr
import pytest

# histogram __init__ values
LOWEST = 1
SCALED_LOWEST = 1000
HIGHEST = 3600 * 1000 * 1000
SIGNIFICANT = 3

# record values
SCALE = 512
INTERVAL = 10000
LOOPS = 10000
VALUE = 1000
HIGHEST_VALUE = 100000000


@pytest.fixture
def simple():
    histogram = hdr.Histogram(LOWEST, HIGHEST, SIGNIFICANT)

    for i in range(LOOPS):
        histogram.record(VALUE)

    histogram.record(HIGHEST_VALUE)

    return histogram


@pytest.fixture
def corrected():
    histogram = hdr.Histogram(LOWEST, HIGHEST, SIGNIFICANT)

    for i in range(LOOPS):
        histogram.corrected(VALUE, INTERVAL)

    histogram.corrected(HIGHEST_VALUE, INTERVAL)

    return histogram


@pytest.fixture
def scaled():
    histogram = hdr.Histogram(SCALED_LOWEST, HIGHEST * SCALE, SIGNIFICANT)

    for i in range(LOOPS):
        histogram.record(VALUE * SCALE)

    histogram.record(HIGHEST_VALUE * SCALE)

    return histogram


@pytest.fixture
def scaled_and_corrected():
    histogram = hdr.Histogram(SCALED_LOWEST, HIGHEST * SCALE, SIGNIFICANT)

    for i in range(LOOPS):
        histogram.corrected(VALUE * SCALE, INTERVAL * SCALE)

    histogram.corrected(HIGHEST_VALUE * SCALE, INTERVAL * SCALE)

    return histogram


def test_create_with_large_values():
    histogram = hdr.Histogram(20000000, 100000000, 5)

    histogram.record(100000000)
    histogram.record(20000000)
    histogram.record(30000000)

    percentile50_00 = histogram.valued_at_percentile(50.0)
    percentile83_33 = histogram.valued_at_percentile(83.33)
    percentile83_34 = histogram.valued_at_percentile(83.34)
    percentile99_00 = histogram.valued_at_percentile(99.0)

    assert histogram.lowest_equivalent(20000000) == histogram.lowest_equivalent(percentile50_00)
    assert histogram.lowest_equivalent(30000000) == histogram.lowest_equivalent(percentile83_33)
    assert histogram.lowest_equivalent(100000000) == histogram.lowest_equivalent(percentile83_34)
    assert histogram.lowest_equivalent(100000000) == histogram.lowest_equivalent(percentile99_00)


def test_invalid_init():
    # Should not allow 0 as lowest trackable value
    with pytest.raises(Exception):
        hdr.Histogram(0, 1024, 2)

    # Should have lowest < 2 * highest
    with pytest.raises(Exception):
        hdr.Histogram(80, 110, 2)

    # Should have 1<significant<5
    with pytest.raises(Exception):
        hdr.Histogram(80, 110, 1)

    with pytest.raises(Exception):
        hdr.Histogram(80, 110, 5)


def test_total_count(simple, corrected):
    assert simple.total() == 10001, 'Total raw count != 10001'
    assert corrected.total() == 20000, 'Total corrected count != 20000'


def test_get_max_value(simple, corrected):
    assert simple.lowest_equivalent(simple.max()) == simple.lowest_equivalent(100000000), "simple.max() != 100000000L"

    msg = "corrected.max() != 100000000L"
    assert corrected.lowest_equivalent(corrected.max()) == corrected.lowest_equivalent(100000000), msg


def test_get_min_value(simple, corrected):
    assert simple.min() == 1000, 'simple.min() != 1000'
    assert corrected.min() == 1000, 'corrected.min() != 1000'


def test_percentiles(simple, corrected):
    assert abs(simple.valued_at_percentile(30.0) - 1000) < 1000 * 0.001, 'Value at 30% not 1000.0'
    assert abs(simple.valued_at_percentile(99.0) - 1000) < 1000 * 0.001, 'Value at 99% not 1000.0'
    assert abs(simple.valued_at_percentile(99.99) - 1000) < 1000 * 0.001, 'Value at 99.99% not 1000.0'
    assert abs(simple.valued_at_percentile(99.999) - 100000000) < 100000000 * 0.001, 'Value at 99.999% not 100000000.0'
    assert abs(simple.valued_at_percentile(100) - 100000000) < 100000000 * 0.001, 'Value at 100% not 100000000.0'

    assert abs(corrected.valued_at_percentile(30.0) - 1000) < 1000 * 0.001, 'Value at 30% not 1000.0'
    assert abs(corrected.valued_at_percentile(50.0) - 1000) < 1000 * 0.001, 'Value at 50% not 1000.0'
    assert abs(corrected.valued_at_percentile(75.0) - 50000000) < 50000000 * 0.001, 'Value at 75% not 50000000.0'
    assert abs(corrected.valued_at_percentile(90.0) - 80000000) < 80000000 * 0.001, 'Value at 90% not 80000000.0'
    assert abs(corrected.valued_at_percentile(99.0) - 98000000) < 98000000 * 0.001, 'Value at 99% not 98000000.0'

    msg = 'Value at 99.999% not 100000000.0'
    assert abs(corrected.valued_at_percentile(99.999) - 100000000) < 100000000 * 0.001, msg

    assert abs(corrected.valued_at_percentile(100) - 100000000) < 100000000 * 0.001, 'Value at 100% not 100000000.0'


def test_recorded_values(simple, corrected):
    iterable = simple.iter('recorded')

    bucket_count = next(iterable)
    assert bucket_count.count == 10000, 'Value at 0 is not 10000'

    bucket_count = next(iterable)
    assert bucket_count.count == 1, 'Value at 1 is not 1'

    with pytest.raises(StopIteration):
        bucket_count = next(iterable)

    iterable = corrected.iter('recorded')

    total = 0
    bucket_count = next(iterable)
    assert bucket_count.count == 10000, 'Value at 0 is not 10000'
    total += bucket_count.count

    for iteration, bucket_count in enumerate(iterable, 1):
        assert bucket_count.count != 0, 'Value at iteration {} must not be 0'.format(iteration)
        total += bucket_count.count

    assert total == 20000, 'Total counts should be 20000'


def test_linear_values(simple, corrected):
    iterable = simple.iter('linear', units_per_bucket=100000)

    bucket_count = next(iterable)
    assert bucket_count.count == 10000, 'Count at 0 is not 10000'

    for iteration, bucket_count in zip(range(998), iterable):
        assert bucket_count.count == 0, 'Count at {} is not 0'.format(iteration)

    # iteration 999
    bucket_count = next(iterable)
    assert bucket_count.count == 1, 'Count at 999 is not 1'

    iterable = corrected.iter('linear', units_per_bucket=10000)
    bucket_count = next(iterable)
    assert bucket_count.count == 10001, 'Count at 0 is not 10001'

    pos = 1
    total = bucket_count.count
    for bucket_count in iterable:
        total += bucket_count.count
        pos += 1

    assert pos == 10000, 'Should of met 10001 values'
    assert total == 20000, 'Should of met 20000 counts'


def test_reset(simple, corrected):
    assert simple.valued_at_percentile(99.0) != 0
    assert corrected.valued_at_percentile(99.0) != 0

    simple.reset()
    corrected.reset()

    assert simple.total() == 0
    assert corrected.total() == 0

    assert simple.valued_at_percentile(99.0) == 0
    assert corrected.valued_at_percentile(99.0) == 0


def test_scaling_equivalence(corrected, scaled_and_corrected):
    correct_scaled_diff = abs(corrected.mean() * SCALE - scaled_and_corrected.mean())

    assert correct_scaled_diff <= scaled_and_corrected.mean() * 0.000001, 'Averages should be equivalent'
    assert corrected.total() == scaled_and_corrected.total(), 'Total count should be equivalent'

    excpected = corrected.valued_at_percentile(99.0) * SCALE
    scaled = scaled_and_corrected.valued_at_percentile(99.0)

    msg = '99% should be equivalent'
    assert corrected.lowest_equivalent(excpected) == scaled_and_corrected.lowest_equivalent(scaled), msg


def test_out_of_range_values():
    histogram = hdr.Histogram(1, 1000, 4)
    histogram.record(32767)

    with pytest.raises(Exception):
        histogram.record(32768)
