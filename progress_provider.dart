import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/models.dart';

class ProgressProvider extends ChangeNotifier {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  
  String? _userId;
  List<UserProgress> _progressHistory = [];
  Set<String> _completedVideoIds = {};
  int _currentStreak = 0;
  int _totalWorkouts = 0;
  bool _isLoading = false;
  
  List<UserProgress> get progressHistory => _progressHistory;
  Set<String> get completedVideoIds => _completedVideoIds;
  int get currentStreak => _currentStreak;
  int get totalWorkouts => _totalWorkouts;
  bool get isLoading => _isLoading;
  
  void setUserId(String userId) {
    _userId = userId;
    _loadProgress();
  }
  
  Future<void> _loadProgress() async {
    if (_userId == null) return;
    
    _isLoading = true;
    notifyListeners();
    
    try {
      // Load progress history
      final snapshot = await _firestore
          .collection('users')
          .doc(_userId)
          .collection('progress')
          .orderBy('completedAt', descending: true)
          .limit(100)
          .get();
      
      _progressHistory = snapshot.docs
          .map((doc) => UserProgress.fromFirestore(doc))
          .toList();
      
      _completedVideoIds = _progressHistory.map((p) => p.videoId).toSet();
      
      // Load user stats
      final userDoc = await _firestore.collection('users').doc(_userId).get();
      if (userDoc.exists) {
        final data = userDoc.data()!;
        _currentStreak = data['currentStreak'] ?? 0;
        _totalWorkouts = data['totalWorkouts'] ?? 0;
      }
    } catch (e) {
      debugPrint('Error loading progress: $e');
    }
    
    _isLoading = false;
    notifyListeners();
  }
  
  Future<void> logWorkout({
    required String videoId,
    int reps = 0,
    double weight = 0,
    String notes = '',
    int timeSeconds = 0,
  }) async {
    if (_userId == null) return;
    
    final progress = UserProgress(
      odId: '',
      oderId: _userId!,
      videoId: videoId,
      completedAt: DateTime.now(),
      reps: reps,
      weight: weight,
      notes: notes,
      timeSeconds: timeSeconds,
    );
    
    try {
      await _firestore
          .collection('users')
          .doc(_userId)
          .collection('progress')
          .add(progress.toMap());
      
      // Update streak and total
      await _updateStreak();
      await _incrementTotalWorkouts();
      
      _completedVideoIds.add(videoId);
      _progressHistory.insert(0, progress);
      notifyListeners();
    } catch (e) {
      debugPrint('Error logging workout: $e');
    }
  }
  
  Future<void> _updateStreak() async {
    if (_userId == null) return;
    
    final today = DateTime.now();
    final yesterday = today.subtract(const Duration(days: 1));
    
    // Check if user worked out yesterday
    final yesterdayStart = DateTime(yesterday.year, yesterday.month, yesterday.day);
    final yesterdayEnd = yesterdayStart.add(const Duration(days: 1));
    
    final snapshot = await _firestore
        .collection('users')
        .doc(_userId)
        .collection('progress')
        .where('completedAt', isGreaterThanOrEqualTo: Timestamp.fromDate(yesterdayStart))
        .where('completedAt', isLessThan: Timestamp.fromDate(yesterdayEnd))
        .limit(1)
        .get();
    
    if (snapshot.docs.isNotEmpty) {
      // Worked out yesterday, increment streak
      _currentStreak++;
    } else {
      // Missed yesterday, check if already worked out today
      final todayStart = DateTime(today.year, today.month, today.day);
      final todaySnapshot = await _firestore
          .collection('users')
          .doc(_userId)
          .collection('progress')
          .where('completedAt', isGreaterThanOrEqualTo: Timestamp.fromDate(todayStart))
          .limit(2)
          .get();
      
      if (todaySnapshot.docs.length <= 1) {
        // First workout today after missing yesterday, reset streak
        _currentStreak = 1;
      }
    }
    
    await _firestore.collection('users').doc(_userId).update({
      'currentStreak': _currentStreak,
    });
  }
  
  Future<void> _incrementTotalWorkouts() async {
    if (_userId == null) return;
    
    _totalWorkouts++;
    await _firestore.collection('users').doc(_userId).update({
      'totalWorkouts': FieldValue.increment(1),
    });
  }
  
  bool hasCompletedVideo(String videoId) {
    return _completedVideoIds.contains(videoId);
  }
  
  List<UserProgress> getProgressForVideo(String videoId) {
    return _progressHistory.where((p) => p.videoId == videoId).toList();
  }
  
  Map<String, int> getWeeklyStats() {
    final now = DateTime.now();
    final weekStart = now.subtract(Duration(days: now.weekday - 1));
    
    final Map<String, int> stats = {
      'Mon': 0, 'Tue': 0, 'Wed': 0, 'Thu': 0, 'Fri': 0, 'Sat': 0, 'Sun': 0,
    };
    
    final days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    
    for (final progress in _progressHistory) {
      if (progress.completedAt.isAfter(weekStart)) {
        final dayIndex = progress.completedAt.weekday - 1;
        if (dayIndex >= 0 && dayIndex < 7) {
          stats[days[dayIndex]] = (stats[days[dayIndex]] ?? 0) + 1;
        }
      }
    }
    
    return stats;
  }
}
