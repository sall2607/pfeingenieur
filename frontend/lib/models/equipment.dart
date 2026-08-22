class Equipment {
  final String id;
  final String name;
  final String designation;
  final String equipmentStatus;
  final String? brand;
  final String? model;
  final String? serialNumber;
  final int? power;
  final int? voltage;
  final double? temperature;
  final int? coolingCapacity;
  final String? location;
  final Map<String, double>? confidence;
  final bool needsReview;
  final String? detectedAt;

  Equipment({
    required this.id,
    required this.name,
    required this.designation,
    required this.equipmentStatus,
    this.brand,
    this.model,
    this.serialNumber,
    this.power,
    this.voltage,
    this.temperature,
    this.coolingCapacity,
    this.location,
    this.confidence,
    required this.needsReview,
    this.detectedAt,
  });

  factory Equipment.fromJson(Map<String, dynamic> json) {
    return Equipment(
      id:              json['id'] ?? '',
      name:            json['name'] ?? '',
      designation:     json['designation'] ?? '',
      equipmentStatus: json['equipmentStatus'] ?? '',
      brand:           json['brand'],
      model:           json['model'],
      serialNumber:    json['serialNumber'],
      power:           json['power'],
      voltage:         json['voltage'],
      temperature:     json['temperature']?.toDouble(),
      coolingCapacity: json['coolingCapacity'],
      location:        json['location'],
      confidence:      json['confidence'] != null
          ? Map<String, double>.from(
              json['confidence'].map(
                (k, v) => MapEntry(k, (v as num).toDouble())
              )
            )
          : null,
      needsReview: json['needsReview'] ?? false,
      detectedAt:  json['detectedAt'],
    );
  }

  Map<String, dynamic> toJson() => {
    'id':              id,
    'name':            name,
    'designation':     designation,
    'equipmentStatus': equipmentStatus,
    'brand':           brand,
    'model':           model,
    'serialNumber':    serialNumber,
    'power':           power,
    'voltage':         voltage,
    'temperature':     temperature,
    'coolingCapacity': coolingCapacity,
    'location':        location,
    'confidence':      confidence,
    'needsReview':     needsReview,
    'detectedAt':      detectedAt,
  };

  // Désignations disponibles
  static const List<String> designations = [
    'AppareilCuisine',
    'AppareilInformatique',
    'Climatisation',
    'Eclairage',
    'Robinet',
    'Refrigeration',
    'PeripheriqueImpression',
    'InfrastructureIT',
    'Autres',
  ];

  // Statuts disponibles
  static const List<String> statuts = [
    'Toujours_en_marche',
    'En_marche_pendant_les_horaires_de_travail',
    'En_marche_selon_un_planning_specifique',
    'En_marche_selon_un_besoin',
    'Mode_saisonnier',
    'Mode_maintenance',
    'NonDetachable',
    'Inactif',
  ];

  // Icône selon la désignation
  String get icon {
    switch (designation) {
      case 'AppareilInformatique':  return '💻';
      case 'Climatisation':         return '❄️';
      case 'AppareilCuisine':       return '🍳';
      case 'Refrigeration':         return '🧊';
      case 'InfrastructureIT':      return '🌐';
      case 'PeripheriqueImpression':return '🖨️';
      case 'Eclairage':             return '💡';
      case 'Robinet':               return '🚿';
      default:                      return '📦';
    }
  }

  // Couleur selon needsReview
  bool get isValid => !needsReview;
}