from __future__ import annotations
import numpy as np
from sklearn.decomposition import TruncatedSVD

class PyODSVDWrapper:
    """
    Accepts the SAME sparse feature matrix your API builds.
    Internally:
      - Applies fitted TruncatedSVD to get low-dim dense features
      - Calls PyOD detector.decision_function (outlier score; higher=worse)
      - Converts to 'normality' score (>0 normal, <0 anomaly), so API keeps threshold=0.0
    """
    def __init__(self, svd: TruncatedSVD, detector):
        self.svd = svd
        self.detector = detector
        if not hasattr(detector, "threshold_"):
            raise ValueError("Detector missing threshold_ (fit with contamination set).")
        self.outlier_threshold_ = float(detector.threshold_)

    def decision_function(self, X):
        Z = self.svd.transform(X)
        out_scores = self.detector.decision_function(Z)  # higher=worse
        normal_scores = self.outlier_threshold_ - out_scores
        return normal_scores

    def predict(self, X):
        Z = self.svd.transform(X)
        y = self.detector.predict(Z)  # 0=inlier, 1=outlier
        return np.where(y == 0, 1, -1)
