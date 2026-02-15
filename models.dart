import 'package:cloud_firestore/cloud_firestore.dart';

// Subscription Tiers
enum SubscriptionTier { free, basic, pro, elite }

extension TierExtension on SubscriptionTier {
  String get name {
    switch (this) {
      case SubscriptionTier.free: return 'Free';
      case SubscriptionTier.basic: return 'Basic';
      case SubscriptionTier.pro: return 'Pro';
      case SubscriptionTier.elite: return 'Elite';
    }
  }
  
  double get monthlyPrice {
    switch (this) {
      case SubscriptionTier.free: return 0;
      case SubscriptionTier.basic: return 9.99;
      case SubscriptionTier.pro: return 19.99;
      case SubscriptionTier.elite: return 49.99;
    }
  }
}

// Position Type
enum PositionType { wr, rb, both }

// Difficulty Level
enum DifficultyLevel { beginner, intermediate, advanced, pro }

// Drill Category
enum DrillCategory {
  routeRunning,
  releaseMoves,
  handsCatching,
  footwork,
  speedConditioning,
  ballCarrying,
  passProtection,
  filmStudy,
  fullWorkout,
}

extension DrillCategoryExtension on DrillCategory {
  String get displayName {
    switch (this) {
      case DrillCategory.routeRunning: return 'Route Running';
      case DrillCategory.releaseMoves: return 'Release Moves';
      case DrillCategory.handsCatching: return 'Hands & Catching';
      case DrillCategory.footwork: return 'Footwork';
      case DrillCategory.speedConditioning: return 'Speed & Conditioning';
      case DrillCategory.ballCarrying: return 'Ball Carrying';
      case DrillCategory.passProtection: return 'Pass Protection';
      case DrillCategory.filmStudy: return 'Film Study';
      case DrillCategory.fullWorkout: return 'Full Workout';
    }
  }
  
  String get icon {
    switch (this) {
      case DrillCategory.routeRunning: return '🏃';
      case DrillCategory.releaseMoves: return '💨';
      case DrillCategory.handsCatching: return '🙌';
      case DrillCategory.footwork: return '👟';
      case DrillCategory.speedConditioning: return '⚡';
      case DrillCategory.ballCarrying: return '🏈';
      case DrillCategory.passProtection: return '🛡️';
      case DrillCategory.filmStudy: return '🎬';
      case DrillCategory.fullWorkout: return '💪';
    }
  }
}

// Video Model
class TrainingVideo {
  final String id;
  final String title;
  final String description;
  final String videoUrl;
  final String thumbnailUrl;
  final DrillCategory category;
  final PositionType position;
  final DifficultyLevel difficulty;
  final SubscriptionTier requiredTier;
  final int durationSeconds;
  final List<String> equipment;
  final List<String> coachingCues;
  final DateTime createdAt;
  
  TrainingVideo({
    required this.id,
    required this.title,
    required this.description,
    required this.videoUrl,
    required this.thumbnailUrl,
    required this.category,
    required this.position,
    required this.difficulty,
    required this.requiredTier,
    required this.durationSeconds,
    required this.equipment,
    required this.coachingCues,
    required this.createdAt,
  });
  
  factory TrainingVideo.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    return TrainingVideo(
      id: doc.id,
      title: data['title'] ?? '',
      description: data['description'] ?? '',
      videoUrl: data['videoUrl'] ?? '',
      thumbnailUrl: data['thumbnailUrl'] ?? '',
      category: DrillCategory.values.firstWhere(
        (e) => e.name == data['category'],
        orElse: () => DrillCategory.fullWorkout,
      ),
      position: PositionType.values.firstWhere(
        (e) => e.name == data['position'],
        orElse: () => PositionType.both,
      ),
      difficulty: DifficultyLevel.values.firstWhere(
        (e) => e.name == data['difficulty'],
        orElse: () => DifficultyLevel.beginner,
      ),
      requiredTier: SubscriptionTier.values.firstWhere(
        (e) => e.name == data['requiredTier'],
        orElse: () => SubscriptionTier.free,
      ),
      durationSeconds: data['durationSeconds'] ?? 0,
      equipment: List<String>.from(data['equipment'] ?? []),
      coachingCues: List<String>.from(data['coachingCues'] ?? []),
      createdAt: (data['createdAt'] as Timestamp?)?.toDate() ?? DateTime.now(),
    );
  }
  
  String get durationFormatted {
    final minutes = durationSeconds ~/ 60;
    final seconds = durationSeconds % 60;
    return '${minutes}:${seconds.toString().padLeft(2, '0')}';
  }
}

// Workout Program Model
class WorkoutProgram {
  final String id;
  final String title;
  final String description;
  final String thumbnailUrl;
  final int weeks;
  final PositionType position;
  final DifficultyLevel difficulty;
  final SubscriptionTier requiredTier;
  final List<WorkoutDay> days;
  
  WorkoutProgram({
    required this.id,
    required this.title,
    required this.description,
    required this.thumbnailUrl,
    required this.weeks,
    required this.position,
    required this.difficulty,
    required this.requiredTier,
    required this.days,
  });
  
  factory WorkoutProgram.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    return WorkoutProgram(
      id: doc.id,
      title: data['title'] ?? '',
      description: data['description'] ?? '',
      thumbnailUrl: data['thumbnailUrl'] ?? '',
      weeks: data['weeks'] ?? 4,
      position: PositionType.values.firstWhere(
        (e) => e.name == data['position'],
        orElse: () => PositionType.both,
      ),
      difficulty: DifficultyLevel.values.firstWhere(
        (e) => e.name == data['difficulty'],
        orElse: () => DifficultyLevel.beginner,
      ),
      requiredTier: SubscriptionTier.values.firstWhere(
        (e) => e.name == data['requiredTier'],
        orElse: () => SubscriptionTier.basic,
      ),
      days: (data['days'] as List<dynamic>?)
          ?.map((d) => WorkoutDay.fromMap(d))
          .toList() ?? [],
    );
  }
}

class WorkoutDay {
  final int dayNumber;
  final String title;
  final List<String> videoIds;
  final int restSeconds;
  
  WorkoutDay({
    required this.dayNumber,
    required this.title,
    required this.videoIds,
    required this.restSeconds,
  });
  
  factory WorkoutDay.fromMap(Map<String, dynamic> map) {
    return WorkoutDay(
      dayNumber: map['dayNumber'] ?? 1,
      title: map['title'] ?? '',
      videoIds: List<String>.from(map['videoIds'] ?? []),
      restSeconds: map['restSeconds'] ?? 60,
    );
  }
}

// User Progress Model
class UserProgress {
  final String odId;
  final String oderId;
  final String videoId;
  final DateTime completedAt;
  final int reps;
  final double weight;
  final String notes;
  final int timeSeconds;
  
  UserProgress({
    required this.odId,
    required this.oderId,
    required this.videoId,
    required this.completedAt,
    this.reps = 0,
    this.weight = 0,
    this.notes = '',
    this.timeSeconds = 0,
  });
  
  factory UserProgress.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    return UserProgress(
      odId: doc.id,
      oderId: data['userId'] ?? '',
      videoId: data['videoId'] ?? '',
      completedAt: (data['completedAt'] as Timestamp?)?.toDate() ?? DateTime.now(),
      reps: data['reps'] ?? 0,
      weight: (data['weight'] ?? 0).toDouble(),
      notes: data['notes'] ?? '',
      timeSeconds: data['timeSeconds'] ?? 0,
    );
  }
  
  Map<String, dynamic> toMap() {
    return {
      'userId': oderId,
      'videoId': videoId,
      'completedAt': Timestamp.fromDate(completedAt),
      'reps': reps,
      'weight': weight,
      'notes': notes,
      'timeSeconds': timeSeconds,
    };
  }
}

// User Model
class AppUser {
  final String id;
  final String email;
  final String displayName;
  final String photoUrl;
  final SubscriptionTier tier;
  final PositionType preferredPosition;
  final int currentStreak;
  final int totalWorkouts;
  final DateTime createdAt;
  
  AppUser({
    required this.id,
    required this.email,
    this.displayName = '',
    this.photoUrl = '',
    this.tier = SubscriptionTier.free,
    this.preferredPosition = PositionType.both,
    this.currentStreak = 0,
    this.totalWorkouts = 0,
    required this.createdAt,
  });
  
  factory AppUser.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    return AppUser(
      id: doc.id,
      email: data['email'] ?? '',
      displayName: data['displayName'] ?? '',
      photoUrl: data['photoUrl'] ?? '',
      tier: SubscriptionTier.values.firstWhere(
        (e) => e.name == data['tier'],
        orElse: () => SubscriptionTier.free,
      ),
      preferredPosition: PositionType.values.firstWhere(
        (e) => e.name == data['preferredPosition'],
        orElse: () => PositionType.both,
      ),
      currentStreak: data['currentStreak'] ?? 0,
      totalWorkouts: data['totalWorkouts'] ?? 0,
      createdAt: (data['createdAt'] as Timestamp?)?.toDate() ?? DateTime.now(),
    );
  }
}
