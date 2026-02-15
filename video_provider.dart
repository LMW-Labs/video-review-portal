import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/models.dart';

class VideoProvider extends ChangeNotifier {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  
  List<TrainingVideo> _videos = [];
  List<WorkoutProgram> _programs = [];
  bool _isLoading = false;
  String? _error;
  
  DrillCategory? _selectedCategory;
  PositionType? _selectedPosition;
  DifficultyLevel? _selectedDifficulty;
  
  List<TrainingVideo> get videos => _filteredVideos;
  List<WorkoutProgram> get programs => _programs;
  bool get isLoading => _isLoading;
  String? get error => _error;
  
  DrillCategory? get selectedCategory => _selectedCategory;
  PositionType? get selectedPosition => _selectedPosition;
  DifficultyLevel? get selectedDifficulty => _selectedDifficulty;
  
  List<TrainingVideo> get _filteredVideos {
    return _videos.where((video) {
      if (_selectedCategory != null && video.category != _selectedCategory) {
        return false;
      }
      if (_selectedPosition != null && 
          video.position != _selectedPosition && 
          video.position != PositionType.both) {
        return false;
      }
      if (_selectedDifficulty != null && video.difficulty != _selectedDifficulty) {
        return false;
      }
      return true;
    }).toList();
  }
  
  List<TrainingVideo> getVideosByCategory(DrillCategory category) {
    return _videos.where((v) => v.category == category).toList();
  }
  
  List<TrainingVideo> getVideosByTier(SubscriptionTier tier) {
    return _videos.where((v) => v.requiredTier.index <= tier.index).toList();
  }
  
  List<TrainingVideo> getFeaturedVideos() {
    return _videos.take(5).toList();
  }
  
  TrainingVideo? getVideoById(String id) {
    try {
      return _videos.firstWhere((v) => v.id == id);
    } catch (_) {
      return null;
    }
  }
  
  Future<void> loadVideos() async {
    if (_videos.isNotEmpty) return;
    
    _isLoading = true;
    notifyListeners();
    
    try {
      final snapshot = await _firestore
          .collection('videos')
          .orderBy('createdAt', descending: true)
          .get();
      
      _videos = snapshot.docs.map((doc) => TrainingVideo.fromFirestore(doc)).toList();
      _error = null;
    } catch (e) {
      _error = e.toString();
    }
    
    _isLoading = false;
    notifyListeners();
  }
  
  Future<void> loadPrograms() async {
    if (_programs.isNotEmpty) return;
    
    _isLoading = true;
    notifyListeners();
    
    try {
      final snapshot = await _firestore
          .collection('programs')
          .orderBy('createdAt', descending: true)
          .get();
      
      _programs = snapshot.docs.map((doc) => WorkoutProgram.fromFirestore(doc)).toList();
      _error = null;
    } catch (e) {
      _error = e.toString();
    }
    
    _isLoading = false;
    notifyListeners();
  }
  
  void setCategory(DrillCategory? category) {
    _selectedCategory = category;
    notifyListeners();
  }
  
  void setPosition(PositionType? position) {
    _selectedPosition = position;
    notifyListeners();
  }
  
  void setDifficulty(DifficultyLevel? difficulty) {
    _selectedDifficulty = difficulty;
    notifyListeners();
  }
  
  void clearFilters() {
    _selectedCategory = null;
    _selectedPosition = null;
    _selectedDifficulty = null;
    notifyListeners();
  }
  
  Future<void> refresh() async {
    _videos = [];
    _programs = [];
    await loadVideos();
    await loadPrograms();
  }
}
