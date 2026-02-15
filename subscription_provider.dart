import 'package:flutter/material.dart';
import 'package:purchases_flutter/purchases_flutter.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/models.dart';

class SubscriptionProvider extends ChangeNotifier {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  
  // RevenueCat API Keys - replace with your actual keys
  static const String _revenueCatApiKeyApple = 'appl_YOUR_KEY_HERE';
  static const String _revenueCatApiKeyGoogle = 'goog_YOUR_KEY_HERE';
  
  SubscriptionTier _currentTier = SubscriptionTier.free;
  List<Package> _availablePackages = [];
  bool _isLoading = false;
  String? _error;
  
  SubscriptionTier get currentTier => _currentTier;
  List<Package> get availablePackages => _availablePackages;
  bool get isLoading => _isLoading;
  String? get error => _error;
  
  bool get isPro => _currentTier.index >= SubscriptionTier.pro.index;
  bool get isElite => _currentTier == SubscriptionTier.elite;
  
  Future<void> init(String oderId) async {
    await Purchases.setLogLevel(LogLevel.debug);
    
    PurchasesConfiguration config;
    // Platform check would go here - simplified for now
    config = PurchasesConfiguration(_revenueCatApiKeyApple);
    
    await Purchases.configure(config..appUserID = oderId);
    
    await _loadSubscriptionStatus();
    await _loadOfferings();
    
    Purchases.addCustomerInfoUpdateListener((customerInfo) {
      _updateTierFromCustomerInfo(customerInfo);
    });
  }
  
  Future<void> _loadSubscriptionStatus() async {
    try {
      final customerInfo = await Purchases.getCustomerInfo();
      _updateTierFromCustomerInfo(customerInfo);
    } catch (e) {
      _error = e.toString();
    }
  }
  
  void _updateTierFromCustomerInfo(CustomerInfo customerInfo) {
    if (customerInfo.entitlements.active.containsKey('elite')) {
      _currentTier = SubscriptionTier.elite;
    } else if (customerInfo.entitlements.active.containsKey('pro')) {
      _currentTier = SubscriptionTier.pro;
    } else if (customerInfo.entitlements.active.containsKey('basic')) {
      _currentTier = SubscriptionTier.basic;
    } else {
      _currentTier = SubscriptionTier.free;
    }
    notifyListeners();
  }
  
  Future<void> _loadOfferings() async {
    try {
      final offerings = await Purchases.getOfferings();
      if (offerings.current != null) {
        _availablePackages = offerings.current!.availablePackages;
      }
    } catch (e) {
      _error = e.toString();
    }
    notifyListeners();
  }
  
  Future<bool> purchasePackage(Package package) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      final customerInfo = await Purchases.purchasePackage(package);
      _updateTierFromCustomerInfo(customerInfo);
      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }
  
  Future<void> restorePurchases() async {
    _isLoading = true;
    notifyListeners();
    
    try {
      final customerInfo = await Purchases.restorePurchases();
      _updateTierFromCustomerInfo(customerInfo);
    } catch (e) {
      _error = e.toString();
    }
    
    _isLoading = false;
    notifyListeners();
  }
  
  bool canAccessVideo(TrainingVideo video) {
    return video.requiredTier.index <= _currentTier.index;
  }
  
  bool canAccessProgram(WorkoutProgram program) {
    return program.requiredTier.index <= _currentTier.index;
  }
  
  SubscriptionTier getRequiredTierForContent(SubscriptionTier contentTier) {
    return contentTier;
  }
  
  Package? getPackageForTier(SubscriptionTier tier) {
    final identifier = tier.name;
    try {
      return _availablePackages.firstWhere(
        (p) => p.identifier.toLowerCase().contains(identifier),
      );
    } catch (_) {
      return null;
    }
  }
}
