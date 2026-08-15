import 'package:flutter/material.dart';

import '../../../data/services/api_client.dart';
import '../../../data/services/api_exception.dart';
import '../theme.dart';

class AuthenticatedPhoto extends StatefulWidget {
  const AuthenticatedPhoto({
    super.key,
    required this.api,
    required this.url,
    required this.fallbackLabel,
    this.radius = 22,
  });

  final ApiClient api;
  final String? url;
  final String fallbackLabel;
  final double radius;

  @override
  State<AuthenticatedPhoto> createState() => _AuthenticatedPhotoState();
}

class _AuthenticatedPhotoState extends State<AuthenticatedPhoto> {
  late final Future<ImageProvider?> _future = _load();

  Future<ImageProvider?> _load() async {
    final url = widget.url;
    if (url == null || url.isEmpty) {
      return null;
    }
    try {
      final response = await widget.api.getBytes(url);
      return MemoryImage(response.bodyBytes);
    } on ApiException {
      return null;
    }
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<ImageProvider?>(
      future: _future,
      builder: (context, snapshot) {
        final image = snapshot.data;
        if (image != null) {
          return CircleAvatar(backgroundImage: image, radius: widget.radius);
        }
        final letter = widget.fallbackLabel.isEmpty
            ? '?'
            : widget.fallbackLabel[0].toUpperCase();
        return CircleAvatar(
          radius: widget.radius,
          backgroundColor: MadrasaTheme.forest,
          child: Text(
            letter,
            style: TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.w700,
              fontSize: widget.radius * 0.7,
            ),
          ),
        );
      },
    );
  }
}
