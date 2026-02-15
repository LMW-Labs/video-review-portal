import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/models.dart';

class AuthProvider extends ChangeNotifier {
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  
  User? _firebaseUser;
  AppUser? _appUser;
  bool _isLoading = true;
  String? _error;
  
  User? get firebaseUser => _firebaseUser;
  AppUser? get appUser => _appUser;
  bool get isLoading => _isLoading;
  bool get isAuthenticated => _firebaseUser != null;
  String? get error => _error;
  
  AuthProvider() {
    _init();
  }
  
  Future<void> _init() async {
    _auth.authStateChanges().listen((user) async {
      _firebaseUser = user;
      if (user != null) {
        await _loadUserData(user.uid);
      } else {
        _appUser = null;
      }
      _isLoading = false;
      notifyListeners();
    });
  }
  
  Future<void> _loadUserData(String odId) async {
    try {
      final doc = await _firestore.collection('users').doc(odId).get();
      if (doc.exists) {
        _appUser = AppUser.fromFirestore(doc);
      }
    } catch (e) {
      _error = e.toString();
    }
  }
  
  Future<bool> signUp({
    required String email,
    required String password,
    required String displayName,
    PositionType position = PositionType.both,
  }) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();
      
      final credential = await _auth.createUserWithEmailAndPassword(
        email: email,
        password: password,
      );
      
      if (credential.user != null) {
        await _firestore.collection('users').doc(credential.user!.uid).set({
          'email': email,
          'displayName': displayName,
          'tier': SubscriptionTier.free.name,
          'preferredPosition': position.name,
          'currentStreak': 0,
          'totalWorkouts': 0,
          'createdAt': FieldValue.serverTimestamp(),
        });
        
        await _loadUserData(credential.user!.uid);
      }
      
      _isLoading = false;
      notifyListeners();
      return true;
    } on FirebaseAuthException catch (e) {
      _error = _getAuthErrorMessage(e.code);
      _isLoading = false;
      notifyListeners();
      return false;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }
  
  Future<bool> signIn({required String email, required String password}) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();
      
      await _auth.signInWithEmailAndPassword(email: email, password: password);
      
      _isLoading = false;
      notifyListeners();
      return true;
    } on FirebaseAuthException catch (e) {
      _error = _getAuthErrorMessage(e.code);
      _isLoading = false;
      notifyListeners();
      return false;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }
  
  Future<void> signOut() async {
    await _auth.signOut();
    _appUser = null;
    notifyListeners();
  }
  
  Future<bool> resetPassword(String email) async {
    try {
      await _auth.sendPasswordResetEmail(email: email);
      return true;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }
  
  Future<void> updateUserPosition(PositionType position) async {
    if (_firebaseUser == null) return;
    
    await _firestore.collection('users').doc(_firebaseUser!.uid).update({
      'preferredPosition': position.name,
    });
    
    await _loadUserData(_firebaseUser!.uid);
    notifyListeners();
  }
  
  String _getAuthErrorMessage(String code) {
    switch (code) {
      case 'email-already-in-use':
        return 'This email is already registered';
      case 'invalid-email':
        return 'Invalid email address';
      case 'weak-password':
        return 'Password is too weak';
      case 'user-not-found':
        return 'No account found with this email';
      case 'wrong-password':
        return 'Incorrect password';
      default:
        return 'An error occurred. Please try again.';
    }
  }
  
  void clearError() {
    _error = null;
    notifyListeners();
  }
}
