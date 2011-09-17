# Based on http://bpbio.googlecode.com/svn/trunk/interval_tree/interval_tree.py

class IntervalTree(object):
  def __init__(self, intervals, depth=16, minbucket=64, _extent=None, maxbucket=512):
    """\
    `intervals` a list of intervals *with start and stop* attributes. Assumed
          to be sorted.
    `depth`   the depth of the tree
    `minbucket` if any node in the tree has fewer than minbucket
          elements, make it a leaf node
    `maxbucket` even it at specifined `depth`, if the number of intervals >
          maxbucket, split the node, make the tree deeper.

    depth and minbucket usually do not need to be changed. if
    dealing with large numbers (> 1M) of intervals, the depth could
    be increased to 24.

    Usage:

     >>> ivals = [Interval(2, 3), Interval(1, 8), Interval(3, 6)]
     >>> tree = IntervalTree(ivals)
     >>> sorted(tree.find(1, 2))
     [Interval(2, 3), Interval(1, 8)]
    """

    depth -= 1
    if (depth == 0 or len(intervals) < minbucket) and len(intervals) < maxbucket:
      self.intervals = intervals
      self.left = self.right = None
      return

    left, right = _extent or \
         (intervals[0].start, max(i.stop for i in intervals))
    center = (left + right) / 2.0

    self.intervals = []
    lefts, rights  = [], []


    for interval in intervals:
      if interval.stop < center:
        lefts.append(interval)
      elif interval.start > center:
        rights.append(interval)
      else: # overlapping.
        self.intervals.append(interval)

    self.left   = lefts  and IntervalTree(lefts,  depth, minbucket, (intervals[0].start,  center)) or None
    self.right  = rights and IntervalTree(rights, depth, minbucket, (center,         right)) or None
    self.center = center


  def find(self, start, stop):
    """find all elements between (or overlapping) start and stop"""
    if self.intervals and not stop < self.intervals[0].start:
      overlapping = [i for i in self.intervals if i.stop >= start
                          and i.start <= stop]
    else:
      overlapping = []

    if self.left and start <= self.center:
      overlapping += self.left.find(start, stop)

    if self.right and stop >= self.center:
      overlapping += self.right.find(start, stop)

    return overlapping
