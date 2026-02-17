"""
Módulo de notificações.
Envia alertas por email sobre eventos importantes.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import streamlit as st


class GerenciadorNotificacoes:
    """Gerencia notificações via email."""
    
    def __init__(self):
        # Configurações de email (usar variáveis de ambiente)
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_remetente = os.getenv("EMAIL_REMETENTE")
        self.senha_email = os.getenv("SENHA_EMAIL")
        
        self.ativo = bool(self.email_remetente and self.senha_email)
    
    def enviar_email(self, destinatario: str, assunto: str, corpo_html: str) -> bool:
        """Envia email.
        
        Args:
            destinatario: Email do destinatário
            assunto: Assunto do email
            corpo_html: Corpo em HTML
            
        Returns:
            True se enviado com sucesso
        """
        if not self.ativo:
            print("⚠️ Email não configurado. Configure SMTP_SERVER, SMTP_PORT, EMAIL_REMETENTE e SENHA_EMAIL.")
            return False
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = assunto
            msg["From"] = self.email_remetente
            msg["To"] = destinatario
            
            # Adicionar versão de texto simples
            corpo_texto = corpo_html.replace("<br>", "\n").replace("<p>", "").replace("</p>", "")
            msg.attach(MIMEText(corpo_texto, "plain"))
            msg.attach(MIMEText(corpo_html, "html"))
            
            # Enviar
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_remetente, self.senha_email)
                server.sendmail(self.email_remetente, [destinatario], msg.as_string())
            
            return True
        
        except Exception as e:
            print(f"❌ Erro ao enviar email: {e}")
            return False
    
    def alerta_pedido_vencido(self, email_cliente: str, pedido_id: int, dias_restantes: int) -> bool:
        """Alerta sobre pedido vencendo.
        
        Args:
            email_cliente: Email do cliente
            pedido_id: ID do pedido
            dias_restantes: Dias até o vencimento
            
        Returns:
            True se enviado
        """
        assunto = f"⚠️ Pedido #{pedido_id} vencendo em {dias_restantes} dias"
        
        corpo = f"""
        <html>
            <body style="font-family: Arial; color: #333;">
                <h2>Alerta de Pedido Vencendo</h2>
                <p>Olá,</p>
                <p>Seu pedido <strong>#{pedido_id}</strong> está vencendo!</p>
                <p style="color: #d9534f; font-size: 16px;">
                    <strong>Dias restantes: {dias_restantes}</strong>
                </p>
                <p>Por favor, verifique o status e tome as ações necessárias.</p>
                <hr>
                <p style="color: #999; font-size: 12px;">
                    Enviado em {datetime.now().strftime('%d/%m/%Y %H:%M')} pelo Sistema JT Pescados
                </p>
            </body>
        </html>
        """
        
        return self.enviar_email(email_cliente, assunto, corpo)
    
    def notificacao_novo_pedido(self, email_admin: str, pedido_id: int, cliente: str, data_entrega: str) -> bool:
        """Notifica admin sobre novo pedido.
        
        Args:
            email_admin: Email do administrador
            pedido_id: ID do pedido
            cliente: Nome do cliente
            data_entrega: Data de entrega
            
        Returns:
            True se enviado
        """
        assunto = f"✅ Novo Pedido #{pedido_id} - {cliente}"
        
        corpo = f"""
        <html>
            <body style="font-family: Arial; color: #333;">
                <h2>Novo Pedido Registrado</h2>
                <table style="border-collapse: collapse; width: 100%;">
                    <tr style="background: #f5f5f5;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>ID Pedido</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{pedido_id}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Cliente</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{cliente}</td>
                    </tr>
                    <tr style="background: #f5f5f5;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Data Entrega</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{data_entrega}</td>
                    </tr>
                </table>
                <p>Verifique o sistema para mais detalhes.</p>
                <hr>
                <p style="color: #999; font-size: 12px;">
                    Enviado em {datetime.now().strftime('%d/%m/%Y %H:%M')} pelo Sistema JT Pescados
                </p>
            </body>
        </html>
        """
        
        return self.enviar_email(email_admin, assunto, corpo)
    
    def notificacao_erro(self, email_admin: str, erro: str, funcao: str, usuario: str = None) -> bool:
        """Notifica admin sobre erro crítico.
        
        Args:
            email_admin: Email do administrador
            erro: Descrição do erro
            funcao: Função onde ocorreu
            usuario: Usuário envolvido
            
        Returns:
            True se enviado
        """
        assunto = f"🚨 ERRO CRÍTICO em {funcao}"
        
        usuario_info = f"<p><strong>Usuário:</strong> {usuario}</p>" if usuario else ""
        
        corpo = f"""
        <html>
            <body style="font-family: Arial; color: #333;">
                <h2 style="color: #d9534f;">ERRO CRÍTICO DETECTADO</h2>
                <p><strong>Função:</strong> {funcao}</p>
                {usuario_info}
                <p><strong>Erro:</strong></p>
                <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto;">
{erro}
                </pre>
                <p style="color: #999; font-size: 12px;">
                    Enviado em {datetime.now().strftime('%d/%m/%Y %H:%M')}
                </p>
            </body>
        </html>
        """
        
        return self.enviar_email(email_admin, assunto, corpo)


# Instância global
notificador = GerenciadorNotificacoes()


def enviar_alerta_validade_pedidos(client, email_admin: str):
    """Verifica pedidos vencidos e envia alertas.
    
    Args:
        client: Cliente Supabase
        email_admin: Email do administrador
    """
    try:
        from datetime import datetime, timedelta
        from core.config import FUSO_BR
        
        # Buscar pedidos que vencemem 7 dias
        response = client.table("pedidos").select("*").execute()
        
        if not response.data:
            return
        
        hoje = datetime.now(FUSO_BR).date()
        
        for pedido in response.data:
            try:
                data_entrega = datetime.strptime(pedido.get("DIA DA ENTREGA", ""), "%d/%m/%Y").date()
                dias_restantes = (data_entrega - hoje).days
                
                # Alertar se estiver vencido ou vencendo em 7 dias
                if 0 <= dias_restantes <= 7:
                    notificador.alerta_pedido_vencido(
                        email_admin,
                        pedido.get("ID_PEDIDO"),
                        dias_restantes
                    )
            except:
                pass
    
    except Exception as e:
        print(f"Erro ao enviar alertas de validade: {e}")
