# -*- coding: utf8 -*-
from collections import namedtuple
import ctypes
from ctypes.util import find_library

hdrlib = ctypes.cdll.LoadLibrary('libhdr_histogram.so')
clib = ctypes.cdll.LoadLibrary(find_library('c'))

cint = ctypes.c_int
cbool = ctypes.c_bool
cdouble = ctypes.c_double

int64 = ctypes.c_int64
int32 = ctypes.c_int32
POINTER = ctypes.POINTER
RangeCount = namedtuple('RangeValue', ('start', 'end', 'count'))
Percentile = namedtuple('Percentile', ('percentile', 'value'))


def function(library, name, arguments_types, return_type=None):
    func = getattr(library, name)
    func.argtypes = arguments_types

    if return_type:
        func.restype = return_type

    return func


class HistogramStruct(ctypes.Structure):
    # <hdr_histogram.h>
    # struct hdr_histogram
    # {
    #     int64 lowest_trackable_value;
    #     int64 highest_trackable_value;
    #     int64 unit_magnitude;
    #     int64 significant_figures;
    #     int32_t sub_bucket_half_count_magnitude;
    #     int32_t sub_bucket_half_count;
    #     int64 sub_bucket_mask;
    #     int32_t sub_bucket_count;
    #     int32_t bucket_count;
    #     int64 min_value;
    #     int64 max_value;
    #     int32_t normalizing_index_offset;
    #     double conversion_ratio;
    #     int32_t counts_len;
    #     int64 total_count;
    #     int64 counts[0];
    # };
    _fields_ = [
        ('lowest_trackable_value', int64),
        ('highest_trackable_value', int64),
        ('unit_magnitude', int64),
        ('significant_figures', int64),
        ('sub_bucket_half_count_magnitude', int32),
        ('sub_bucket_half_count', int32),
        ('sub_bucket_mask', int64),
        ('sub_bucket_count', int32),
        ('bucket_count', int32),
        ('min_value', int64),
        ('max_value', int64),
        ('normalizing_index_offset', int32),
        ('conversion_ratio', cdouble),
        ('counts_len', int32),
        ('total_count', int64),
        ('counts', POINTER(int64)),
    ]


HistogramPointer = POINTER(HistogramStruct)


class IterPercentilesStruct(ctypes.Structure):
    # struct hdr_iter_percentiles {
    #     bool seen_last_value;
    #     int32_t ticks_per_half_distance;
    #     double percentile_to_iterate_to;
    #     double percentile;
    # };
    _fields_ = [
        ('seen_last_value', cbool),
        ('ticks_per_half_distance', int32),
        ('percentile_to_iterate_to', cdouble),
        ('percentile', cdouble),
    ]


class IterRecordedStruct(ctypes.Structure):
    # struct hdr_iter_recorded {
    #     int64 count_added_in_this_iteration_step;
    # };
    _fields_ = [
        ('count_added_in_this_iteration_step', int64),
    ]


class IterLinearStruct(ctypes.Structure):
    # struct hdr_iter_linear {
    #     int64 value_units_per_bucket;
    #     int64 count_added_in_this_iteration_step;
    #     int64 next_value_reporting_level;
    #     int64 next_value_reporting_level_lowest_equivalent;
    # };
    _fields_ = [
        ('value_units_per_bucket', int64),
        ('count_added_in_this_iteration_step', int64),
        ('next_value_reporting_level', int64),
        ('next_value_reporting_level_lowest_equivalent', int64),
    ]


class IterLogStruct(ctypes.Structure):
    # struct hdr_iter_log {
    #     int64 value_units_first_bucket;
    #     double log_base;
    #     int64 count_added_in_this_iteration_step;
    #     int64 next_value_reporting_level;
    #     int64 next_value_reporting_level_lowest_equivalent;
    # };
    _fields_ = [
        ('value_units_first_bucket', int64),
        ('log_base', cdouble),
        ('count_added_in_this_iteration_step', int64),
        ('next_value_reporting_level', int64),
        ('next_value_reporting_level_lowest_equivalent', int64),
    ]


class SpecificsUnion(ctypes.Union):
    # union {
    #     struct hdr_iter_percentiles percentiles;
    #     struct hdr_iter_recorded recorded;
    #     struct hdr_iter_linear linear;
    #     struct hdr_iter_log log;
    # } specifics;
    _fields_ = [
        ('percentiles', IterPercentilesStruct),
        ('recorded', IterRecordedStruct),
        ('linear', IterLinearStruct),
        ('log', IterLogStruct),
    ]


class IteratorStruct(ctypes.Structure):
    # struct hdr_iter {
    #     struct hdr_histogram* h;
    #     int32_t bucket_index;
    #     int32_t sub_bucket_index;
    #     int64 count_at_index;
    #     int64 count_to_index;
    #     int64 value_from_index;
    #     int64 highest_equivalent_value;
    #     union {
    #         struct hdr_iter_percentiles percentiles;
    #         struct hdr_iter_recorded recorded;
    #         struct hdr_iter_linear linear;
    #         struct hdr_iter_log log;
    #     } specifics;
    #     bool (*_next_fp)(struct hdr_iter* iter);
    # };
    pass

# bool (*_next_fp)(struct hdr_iter* iter);
NEXTFP = ctypes.CFUNCTYPE(cbool, POINTER(IteratorStruct))

IteratorStruct._fields_ = [
    ('h', HistogramPointer),
    ('bucket_index', int32),
    ('sub_bucket_index', int32),
    ('count_at_index', int64),
    ('count_to_index', int64),
    ('value_from_index', int64),
    ('highest_equivalent_value', int64),
    ('specifics', SpecificsUnion),
    ('_next_fp', NEXTFP),
]


# int hdr_init(int64_t, int64_t, int, struct hdr_histogram**);
hdr_init = function(hdrlib, 'hdr_init', [int64, int64, cint, POINTER(HistogramPointer)], cint)

# void hdr_reset(struct hdr_histogram*);
hdr_reset = function(hdrlib, 'hdr_reset', [HistogramPointer])

# (we dont have a hdr_free)

# bool hdr_record_value(struct hdr_histogram*, int64_t);
hdr_record_value = function(hdrlib, 'hdr_record_value', [HistogramPointer, int64], cbool)

# bool hdr_record_value(struct hdr_histogram*, int64_t);
hdr_record_value_repeat = function(hdrlib, 'hdr_record_values', [HistogramPointer, int64], cbool)

# bool hdr_record_corrected_value(struct hdr_histogram*, int64_t, int64_t);
hdr_record_corrected_value = function(hdrlib, 'hdr_record_corrected_value', [HistogramPointer, int64, int64], cbool)

# int64_t hdr_add(struct hdr_histogram*, struct hdr_histogram*);
hdr_add = function(hdrlib, 'hdr_add', [HistogramPointer, HistogramPointer], int64)

# int64_t hdr_lowest_equivalent_value(struct hdr_histogram*, int64_t);
hdr_lowest_equivalent_value = function(hdrlib, 'hdr_lowest_equivalent_value', [HistogramPointer, int64], int64)

# int64_t hdr_max(struct hdr_histogram*);
hdr_max = function(hdrlib, 'hdr_max', [HistogramPointer], int64)

# double hdr_mean(struct hdr_histogram*);
hdr_mean = function(hdrlib, 'hdr_mean', [HistogramPointer], cdouble)

# int64_t hdr_min(struct hdr_histogram*);
hdr_min = function(hdrlib, 'hdr_min', [HistogramPointer], int64)

# double hdr_stddev(struct hdr_histogram*)
hdr_stddev = function(hdrlib, 'hdr_stddev', [HistogramPointer], cdouble)

# int64_t hdr_value_at_percentile(struct hdr_histogram*, double);
hdr_value_at_percentile = function(hdrlib, 'hdr_value_at_percentile', [HistogramPointer, cdouble], int64)

# void hdr_iter_init(struct hdr_iter*, struct hdr_histogram*);
hdr_iter_init = function(hdrlib, 'hdr_iter_init', [POINTER(IteratorStruct), HistogramPointer])

# void hdr_iter_percentile_init(struct hdr_iter*, struct hdr_histogram*, int32_t);
hdr_iter_percentile_init = function(
    hdrlib,
    'hdr_iter_percentile_init',
    [POINTER(IteratorStruct), HistogramPointer, int32]
)

# void hdr_iter_recorded_init(struct hdr_iter*, struct hdr_histogram*);
hdr_iter_recorded_init = function(hdrlib, 'hdr_iter_recorded_init', [POINTER(IteratorStruct), HistogramPointer])

# void hdr_iter_linear_init(struct hdr_iter*, struct hdr_histogram*, int64_t);
hdr_iter_linear_init = function(hdrlib, 'hdr_iter_linear_init', [POINTER(IteratorStruct), HistogramPointer, int64])

# void hdr_iter_log_init( struct hdr_iter*, struct hdr_histogram*, int64_t, double);
hdr_iter_log_init = function(hdrlib, 'hdr_iter_log_init', [POINTER(IteratorStruct), HistogramPointer, int64, cdouble])

# bool hdr_iter_next(struct hdr_iter*);
hdr_iter_next = function(hdrlib, 'hdr_iter_next', [POINTER(IteratorStruct)], cbool)


class HistogramIterator(object):
    def __init__(self, histogramref, itertype='basic', units_per_bucket=None):
        self.iterator = IteratorStruct()
        self.iteratorref = ctypes.byref(self.iterator)
        self.histogramref = histogramref
        self.itertype = itertype

        if self.itertype == 'basic':
            hdr_iter_init(self.iteratorref, self.histogramref)
        elif self.itertype == 'recorded':
            hdr_iter_recorded_init(self.iteratorref, self.histogramref)
        elif self.itertype == 'linear':
            if units_per_bucket is None:
                raise Exception('The linear iterator must have units_per_bucket specified')
            hdr_iter_linear_init(self.iteratorref, self.histogramref, int64(units_per_bucket))
        else:
            raise NotImplemented()
        # elif itertype == 'percentile':
        #     hdr_iter_percentile_init(self.iterator, self.histogramref)
        # elif itertype == 'log':
        #     hdr_iter_log_init(self.iterator, self.histogramref)

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        if not hdr_iter_next(self.iteratorref):
            raise StopIteration()

        if self.itertype == 'basic':
            return RangeCount(
                self.iterator.value_from_index,
                self.iterator.highest_equivalent_value,
                self.iterator.count_at_index,
            )
        if self.itertype == 'recorded':
            return RangeCount(
                self.iterator.value_from_index,
                self.iterator.highest_equivalent_value,
                # self.iterator.specifis.recorded.count_added_in_this_iteration_step,
                self.iterator.count_at_index,
            )
        if self.itertype == 'linear':
            return RangeCount(
                self.iterator.value_from_index,
                self.iterator.highest_equivalent_value,
                self.iterator.specifics.linear.count_added_in_this_iteration_step,
            )
        elif self.itertype == 'percentile':
            return Percentile(
                self.iterator.specifics.percentile.percentile,
                self.iterator.highest_equivalent_value,
            )

        raise NotImplemented()


class Histogram(object):
    def __init__(self, lowest, highest, significant):
        self.lowest = lowest
        self.highest = highest
        self.significant = significant
        self.histogram = histogram = POINTER(HistogramStruct)()

        if lowest < 1:
            raise Exception('lowest must be larger than 1')

        if lowest * 2 > highest:
            raise Exception('lowest cannot be larger than highest/2')

        if not (1 < significant < 6):
            raise Exception('significant must be between 1 and 6 (non inclusive)')

        # return non zero on erro (EINVAL)
        if hdr_init(int64(lowest), int64(highest), cint(significant), histogram):
            raise Exception('Invalid arguments')

    def __del__(self):
        clib.free(self.histogram)

    def __iadd__(self, other):
        hdr_add(self.histogram, other.histogram)

    def __iter__(self):
        return self.iter('basic')

    def iter(self, itertype='basic', units_per_bucket=None):
        return HistogramIterator(self.histogram, itertype, units_per_bucket=units_per_bucket)

    # def __len__(self):
    #     return self.histogram.contents.counts_len

    def __getitem__(self, key):
        if type(key) is not int:
            raise IndexError

        if key < 0 or key > self.histogram.counts_len:
            raise IndexError

        raise NotImplemented()

    def reset(self):
        hdr_reset(self.histogram)

    def record(self, value):
        if not hdr_record_value(self.histogram, int64(value)):
            msg = 'value {} is too large (>{}), it cannot be tracked (try increasing significant)'.format(
                value,
                self.histogram.contents.highest_trackable_value
            )
            raise Exception(msg)

    def corrected(self, value, interval):
        if not hdr_record_corrected_value(self.histogram, int64(value), int64(interval)):
            msg = 'value {} is too large (>{}), it cannot be tracked (try increasing significant)'.format(
                value,
                self.histogram.contents.highest_trackable_value
            )
            raise Exception(msg)

    def record_repeat(self, value, times):
        hdr_record_value_repeat(self.histogram, int64(value), int64(times))

    def min(self):
        return hdr_min(self.histogram)

    def max(self):
        return hdr_max(self.histogram)

    def mean(self):
        return hdr_mean(self.histogram)

    def stddev(self):
        return hdr_stddev(self.histogram)

    def valued_at_percentile(self, percentile):
        return hdr_value_at_percentile(self.histogram, cdouble(percentile))

    def lowest_equivalent(self, value):
        return hdr_lowest_equivalent_value(self.histogram, int64(value))

    def total(self):
        return self.histogram.contents.total_count
