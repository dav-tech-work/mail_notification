#!/usr/bin/env python3
"""
Script de instalación y configuración del monitor de correos
"""
import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional


class SetupManager:
    """Gestor de instalación y configuración"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.config_file = self.project_root / ".env"
        self.sender_groups_file = self.project_root / "sender_groups.json"
        self.example_config = self.project_root / "config.example"

    def check_python_version(self) -> bool:
        """Verifica que la versión de Python sea compatible"""
        if sys.version_info < (3, 8):
            print("❌ Error: Se requiere Python 3.8 o superior")
            return False
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detectado")
        return True

    def install_dependencies(self) -> bool:
        """Instala las dependencias del proyecto"""
        try:
            print("📦 Instalando dependencias...")
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    str(self.project_root / "requirements.txt"),
                ],
                check=True,
            )
            print("✅ Dependencias instaladas correctamente")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error instalando dependencias: {e}")
            return False

    def create_directories(self) -> bool:
        """Crea los directorios necesarios"""
        try:
            directories = ["logs", "data", "monitoring"]
            for directory in directories:
                dir_path = self.project_root / directory
                dir_path.mkdir(exist_ok=True)
                print(f"📁 Directorio creado: {directory}")
            return True
        except Exception as e:
            print(f"❌ Error creando directorios: {e}")
            return False

    def setup_configuration(self) -> bool:
        """Configura el archivo .env"""
        if self.config_file.exists():
            response = input(
                "⚠️ El archivo .env ya existe. ¿Deseas sobrescribirlo? (y/N): "
            )
            if response.lower() != "y":
                print("📝 Manteniendo configuración existente")
                return True

        print("🔧 Configurando variables de entorno...")

        config = {}

        # Configuración del servidor IMAP
        print("\n📧 Configuración del servidor de correo:")
        config["IMAP_SERVER"] = input("Servidor IMAP (ej: imap.gmail.com): ").strip()
        config["MAIL"] = input("Dirección de correo: ").strip()
        config["PASS"] = input("Contraseña de aplicación: ").strip()

        # Configuración de Telegram
        print("\n📱 Configuración de Telegram:")
        config["TELEGRAM_TOKEN"] = input("Token del bot de Telegram: ").strip()
        config["TELEGRAM_CHAT_ID"] = input("ID del chat de Telegram: ").strip()

        # Configuración opcional
        print("\n⚙️ Configuración opcional:")
        notify_domains = input(
            "Dominios de notificación (separados por comas, opcional): "
        ).strip()
        if notify_domains:
            config["NOTIFY_DOMAINS"] = notify_domains

        label_candidates = input(
            "Etiquetas de clasificación (opcional, default: Urgente,Importante,Otros): "
        ).strip()
        if label_candidates:
            config["LABEL_CANDIDATES"] = label_candidates
        else:
            config["LABEL_CANDIDATES"] = "Urgente,Importante,Otros"

        # Configuración de logging
        log_level = input(
            "Nivel de logging (DEBUG/INFO/WARNING/ERROR, default: INFO): "
        ).strip()
        if log_level:
            config["LOG_LEVEL"] = log_level
        else:
            config["LOG_LEVEL"] = "INFO"

        # Escribir archivo .env
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                for key, value in config.items():
                    f.write(f"{key}={value}\n")
            print("✅ Archivo .env creado correctamente")
            return True
        except Exception as e:
            print(f"❌ Error creando archivo .env: {e}")
            return False

    def setup_sender_groups(self) -> bool:
        """Configura los grupos de remitentes"""
        if self.sender_groups_file.exists():
            response = input(
                "⚠️ El archivo sender_groups.json ya existe. ¿Deseas sobrescribirlo? (y/N): "
            )
            if response.lower() != "y":
                print("📝 Manteniendo grupos existentes")
                return True

        print("👥 Configurando grupos de remitentes...")

        groups = {}
        while True:
            group_name = input("\nNombre del grupo (o 'fin' para terminar): ").strip()
            if group_name.lower() == "fin":
                break

            emails = []
            print(f"Agregando emails para el grupo '{group_name}':")
            while True:
                email = input("Email (o 'fin' para terminar el grupo): ").strip()
                if email.lower() == "fin":
                    break
                if email:
                    emails.append(email)

            if emails:
                groups[group_name] = emails

        # Escribir archivo JSON
        try:
            with open(self.sender_groups_file, "w", encoding="utf-8") as f:
                json.dump(groups, f, indent=2, ensure_ascii=False)
            print("✅ Archivo sender_groups.json creado correctamente")
            return True
        except Exception as e:
            print(f"❌ Error creando sender_groups.json: {e}")
            return False

    def run_tests(self) -> bool:
        """Ejecuta las pruebas del proyecto"""
        try:
            print("🧪 Ejecutando pruebas...")
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/test_main.py", "-v"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("✅ Todas las pruebas pasaron")
                return True
            else:
                print("❌ Algunas pruebas fallaron:")
                print(result.stdout)
                print(result.stderr)
                return False
        except Exception as e:
            print(f"❌ Error ejecutando pruebas: {e}")
            return False

    def test_telegram_connection(self) -> bool:
        """Prueba la conexión a Telegram"""
        try:
            print("📱 Probando conexión a Telegram...")
            result = subprocess.run(
                [sys.executable, str(self.project_root / "main.py"), "test_telegram"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("✅ Conexión a Telegram exitosa")
                return True
            else:
                print("❌ Error en conexión a Telegram:")
                print(result.stderr)
                return False
        except Exception as e:
            print(f"❌ Error probando Telegram: {e}")
            return False

    def create_systemd_service(self) -> bool:
        """Crea un servicio systemd para el monitor"""
        try:
            service_content = f"""[Unit]
Description=Email Monitor Service
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'root')}
WorkingDirectory={self.project_root}
Environment=PATH={self.project_root}/venv/bin
ExecStart={self.project_root}/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

            service_file = f"/etc/systemd/system/email-monitor.service"

            response = input(
                f"¿Deseas crear el servicio systemd en {service_file}? (y/N): "
            )
            if response.lower() == "y":
                # Requiere permisos de sudo
                with open("/tmp/email-monitor.service", "w") as f:
                    f.write(service_content)

                subprocess.run(
                    ["sudo", "cp", "/tmp/email-monitor.service", service_file]
                )
                subprocess.run(["sudo", "systemctl", "daemon-reload"])
                subprocess.run(["sudo", "systemctl", "enable", "email-monitor.service"])

                print("✅ Servicio systemd creado y habilitado")
                print("Para iniciar el servicio: sudo systemctl start email-monitor")
                return True
            else:
                print("📝 Servicio systemd no creado")
                return True
        except Exception as e:
            print(f"❌ Error creando servicio systemd: {e}")
            return False

    def run_setup(self) -> bool:
        """Ejecuta el proceso completo de configuración"""
        print("🚀 Iniciando configuración del monitor de correos...\n")

        steps = [
            ("Verificar versión de Python", self.check_python_version),
            ("Crear directorios", self.create_directories),
            ("Instalar dependencias", self.install_dependencies),
            ("Configurar variables de entorno", self.setup_configuration),
            ("Configurar grupos de remitentes", self.setup_sender_groups),
            ("Ejecutar pruebas", self.run_tests),
            ("Probar conexión a Telegram", self.test_telegram_connection),
            ("Crear servicio systemd", self.create_systemd_service),
        ]

        for step_name, step_func in steps:
            print(f"\n{'='*50}")
            print(f"Paso: {step_name}")
            print(f"{'='*50}")

            if not step_func():
                print(f"\n❌ Error en: {step_name}")
                response = input("¿Deseas continuar con el siguiente paso? (y/N): ")
                if response.lower() != "y":
                    return False

        print(f"\n{'='*50}")
        print("🎉 Configuración completada exitosamente!")
        print(f"{'='*50}")
        print("\n📋 Próximos pasos:")
        print("1. Revisar la configuración en .env")
        print("2. Ajustar sender_groups.json si es necesario")
        print("3. Ejecutar: python main.py")
        print("4. Para usar Docker: docker-compose up -d")
        print("5. Para usar systemd: sudo systemctl start email-monitor")

        return True


def main():
    """Función principal"""
    setup = SetupManager()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "test":
            setup.run_tests()
        elif command == "telegram":
            setup.test_telegram_connection()
        elif command == "config":
            setup.setup_configuration()
        elif command == "groups":
            setup.setup_sender_groups()
        else:
            print(f"Comando desconocido: {command}")
            print("Comandos disponibles: test, telegram, config, groups")
            sys.exit(1)
    else:
        setup.run_setup()


if __name__ == "__main__":
    main()
