import 'package:flutter/material.dart';

import '../../../core/copy.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/accent_card.dart';
import '../view_models/auth_view_model.dart';

class LoginView extends StatefulWidget {
  const LoginView({super.key, required this.viewModel});

  final AuthViewModel viewModel;

  @override
  State<LoginView> createState() => _LoginViewState();
}

class _LoginViewState extends State<LoginView> {
  final _username = TextEditingController();
  final _password = TextEditingController();
  String? _localError;

  @override
  void dispose() {
    _username.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final username = _username.text.trim();
    final password = _password.text;
    if (username.isEmpty) {
      setState(() => _localError = MadrasaCopy.needUsername);
      return;
    }
    if (password.isEmpty) {
      setState(() => _localError = MadrasaCopy.needPassword);
      return;
    }
    setState(() => _localError = null);
    await widget.viewModel.login(username: username, password: password);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // Web: mandhari yenye radial-gradient laini juu ya bg-color.
      body: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFFE9F1EB), MadrasaTheme.paper, Color(0xFFF3ECDF)],
            stops: [0.0, 0.5, 1.0],
          ),
        ),
        child: SafeArea(
          child: ListenableBuilder(
            listenable: widget.viewModel,
            builder: (context, _) {
              final error = _localError ?? widget.viewModel.error;
              return Center(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(20),
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 420),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        _LoginCard(
                          username: _username,
                          password: _password,
                          error: error,
                          busy: widget.viewModel.busy,
                          onSubmit: _submit,
                        ),
                        const SizedBox(height: 25),
                        Text(
                          '© ${DateTime.now().year} ${MadrasaCopy.footer}',
                          textAlign: TextAlign.center,
                          style: const TextStyle(
                            fontSize: 13,
                            color: MadrasaTheme.muted,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );
  }
}

class _LoginCard extends StatelessWidget {
  const _LoginCard({
    required this.username,
    required this.password,
    required this.error,
    required this.busy,
    required this.onSubmit,
  });

  final TextEditingController username;
  final TextEditingController password;
  final String? error;
  final bool busy;
  final VoidCallback onSubmit;

  @override
  Widget build(BuildContext context) {
    return TopAccentCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Center(child: _LoginLogo()),
          const SizedBox(height: 20),
          Text(
            MadrasaCopy.brand,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontFamily: MadrasaTheme.brandFont,
              fontSize: 22,
              fontWeight: FontWeight.w700,
              color: MadrasaTheme.title,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            MadrasaCopy.welcome,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 25,
              fontWeight: FontWeight.w800,
              color: MadrasaTheme.ink,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            MadrasaCopy.subtitle,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 15, color: MadrasaTheme.muted),
          ),
          const SizedBox(height: 30),
          if (error != null) ...[
            _ErrorAlert(message: error!),
            const SizedBox(height: 20),
          ],
          _LabeledField(
            label: MadrasaCopy.username,
            child: TextField(
              key: const Key('login_username'),
              controller: username,
              textInputAction: TextInputAction.next,
              autofillHints: const [AutofillHints.username],
              decoration: const InputDecoration(
                hintText: 'Mfano: Ustadh_Mwalimu',
              ),
            ),
          ),
          const SizedBox(height: 20),
          _LabeledField(
            label: MadrasaCopy.password,
            child: TextField(
              key: const Key('login_password'),
              controller: password,
              obscureText: true,
              onSubmitted: (_) => onSubmit(),
              autofillHints: const [AutofillHints.password],
              decoration: const InputDecoration(hintText: '••••••••'),
            ),
          ),
          const SizedBox(height: 20),
          FilledButton(
            key: const Key('login_submit'),
            onPressed: busy ? null : onSubmit,
            child: busy
                ? const SizedBox(
                    height: 22,
                    width: 22,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Colors.white,
                    ),
                  )
                : Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: const [
                      Text(MadrasaCopy.login),
                      SizedBox(width: 10),
                      Icon(Icons.login, size: 18),
                    ],
                  ),
          ),
        ],
      ),
    );
  }
}

class _LoginLogo extends StatelessWidget {
  const _LoginLogo();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 100,
      height: 100,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: MadrasaTheme.surfaceMuted,
        border: Border.all(color: MadrasaTheme.border, width: 3),
        boxShadow: const [
          BoxShadow(
            color: Color(0x1A000000),
            blurRadius: 15,
            offset: Offset(0, 4),
          ),
        ],
      ),
      clipBehavior: Clip.antiAlias,
      child: Image.asset(
        'assets/images/logo.png',
        fit: BoxFit.cover,
        errorBuilder: (context, error, stack) => const Center(
          child: Icon(Icons.mosque, size: 48, color: MadrasaTheme.primary),
        ),
      ),
    );
  }
}

class _LabeledField extends StatelessWidget {
  const _LabeledField({required this.label, required this.child});

  final String label;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: MadrasaTheme.muted,
          ),
        ),
        const SizedBox(height: 8),
        child,
      ],
    );
  }
}

class _ErrorAlert extends StatelessWidget {
  const _ErrorAlert({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 12),
      decoration: BoxDecoration(
        color: MadrasaTheme.dangerBg,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: MadrasaTheme.dangerBorder),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(
            Icons.error_outline,
            size: 20,
            color: MadrasaTheme.dangerText,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w500,
                color: MadrasaTheme.dangerText,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
