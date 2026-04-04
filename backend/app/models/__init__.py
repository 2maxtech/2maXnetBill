# Import all models here so SQLAlchemy can resolve all relationships at mapper configuration time.
from app.models.bandwidth_usage import BandwidthUsage  # noqa: F401
from app.models.customer import Customer  # noqa: F401
from app.models.customer_activity import CustomerActivity  # noqa: F401
from app.models.disconnect_log import DisconnectLog  # noqa: F401
from app.models.invoice import Invoice  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.payment import Payment  # noqa: F401
from app.models.plan import Plan  # noqa: F401
from app.models.pppoe_session import PPPoESession  # noqa: F401
from app.models.session_traffic import SessionTraffic  # noqa: F401
from app.models.router import Area, Router  # noqa: F401
from app.models.user import User  # noqa: F401
