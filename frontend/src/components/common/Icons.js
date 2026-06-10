/**
 * components/common/Icons.js
 * Centralised collection of lightweight React inline SVG icons.
 * Standardised at 16px size and dynamically inheriting text colors.
 */
import React from 'react';

const baseSvgProps = {
  xmlns: 'http://www.w3.org/2000/svg',
  fill: 'none',
  viewBox: '0 0 24 24',
  strokeWidth: 2,
  stroke: 'currentColor',
};

const getBaseStyle = (customStyle) => ({
  width: 16,
  height: 16,
  display: 'inline-block',
  verticalAlign: 'middle',
  ...customStyle,
});

export const EditIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L6.832 19.82a4.5 4.5 0 0 1-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 0 1 1.13-1.897L16.863 4.487Zm0 0L19.5 7.125" />
  </svg>
);

export const TrashIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
  </svg>
);

export const PaperclipIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="m18.375 12.739-7.693 7.693a4.5 4.5 0 0 1-6.364-6.364l10.94-10.94A3 3 0 1 1 19.5 7.372L8.552 18.32m.009-.01-.01.01m5.625-13.606-7.07 7.071" />
  </svg>
);

export const DownloadIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
  </svg>
);

export const UploadIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
  </svg>
);

export const PlusIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
  </svg>
);

export const SearchIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.604 10.604Z" />
  </svg>
);

export const CheckIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
  </svg>
);

export const CloseIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
  </svg>
);

export const SaveIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 3.75V16.5L12 14.25 7.5 16.5V3.75m9 0H18A2.25 2.25 0 0 1 20.25 6v12A2.25 2.25 0 0 1 18 20.25H6A2.25 2.25 0 0 1 3.75 18V6A2.25 2.25 0 0 1 6 3.75h1.5m9 0h-9" />
  </svg>
);

export const LockIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
  </svg>
);

export const RefreshIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
  </svg>
);

export const ChartBarIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v5.25c0 .621-.504 1.125-1.125 1.125h-2.25A1.125 1.125 0 0 1 3 18.375v-5.25ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125v-9.75ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v14.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
  </svg>
);

export const UsersIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" />
  </svg>
);

export const BuildingIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" />
  </svg>
);

export const CalendarIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" />
  </svg>
);

export const ClockIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
  </svg>
);

export const ClipboardCheckIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 0 3 6.108V16.5A2.25 2.25 0 0 0 5.25 18.75h1.75m.75-16.5h.008v.008H8.25V2.25Z" />
  </svg>
);

export const UserGroupIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 0 0 3.741-.479 3 3 0 0 0-4.682-2.72m.94 3.198.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0 1 12 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 0 1 6 18.719m12 0a5.971 5.971 0 0 0-.941-3.197m0 0A5.995 5.995 0 0 0 12 12.75a5.995 5.995 0 0 0-5.058 2.772m0 0a3 3 0 0 0-4.681 2.72 8.986 8.986 0 0 0 3.74.477m.94-3.197a5.971 5.971 0 0 0-.94 3.197M15 6.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm6 2.25a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Zm-13.5 0a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Z" />
  </svg>
);

export const CogIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.43l-1.003.828c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.43l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 0 1 0-.255c.007-.378-.138-.75-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
  </svg>
);

export const AcademyIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M4.26 10.147a60.436 60.436 0 0 0-.491 6.347A48.62 48.62 0 0 1 12 20.9c2.79 0 5.437-.451 7.907-1.28.196-.066.38-.177.49-.346a60.443 60.443 0 0 0-.49-6.348m-15.657 0a60.39 60.39 0 0 1 5.814-5.519m11.3 5.519a60.39 60.39 0 0 0-5.814-5.519m-7.098 11.697v3.375C8.25 19.75 12 22 12 22s3.75-2.25 3.75-4.428V14.15m-11.69-.176a9.75 9.75 0 0 0-2.316-.308L12 3.75l7.94 6.223c.337.081.62.274.803.557l-1.377 1.884a2.25 2.25 0 0 1-1.953.876H5.05a2.25 2.25 0 0 1-1.954-.876l-1.37-1.884Z" />
  </svg>
);

export const UserIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
  </svg>
);

export const LogoutIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15M12 9l-3 3m0 0 3 3m-3-3h12.75" />
  </svg>
);

export const HomeIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="m2.25 12 8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
  </svg>
);

export const InboxIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 13.5h3.86a2.25 2.25 0 0 1 2.008 1.24l.885 1.77a2.25 2.25 0 0 0 2.007 1.24h1.98a2.25 2.25 0 0 0 2.007-1.24l.885-1.77a2.25 2.25 0 0 1 2.007-1.24h3.89m-18 0h18m-18 0v-2.25A2.25 2.25 0 0 1 4.5 9h15A2.25 2.25 0 0 1 21 11.25v2.25m-18 0v4.5A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75v-4.5" />
  </svg>
);

export const MapPinIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1 1 15 0Z" />
  </svg>
);

export const FlagIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M3 3v1.5M3 21v-6m0 0 2.77-.693a9 9 0 0 1 6.208.682l.108.054a9 9 0 0 0 6.086.71l3.114-.732a48.524 48.524 0 0 0 0-5.594l-3.113.732a9 9 0 0 1-6.085-.711l-.108-.054a9 9 0 0 0-6.208-.682L3 9.5m0 5.5V9.5" />
  </svg>
);

export const LinkIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M13.19 8.688a4.5 4.5 0 0 1 1.242 7.244l-4.5 4.5a4.5 4.5 0 0 1-6.364-6.364l1.757-1.757m13.35-.622 1.757-1.757a4.5 4.5 0 0 0-6.364-6.364l-4.5 4.5a4.5 4.5 0 0 0 1.242 7.244" />
  </svg>
);

export const SignalIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 18.75a1.5 1.5 0 0 1-3 0 1.5 1.5 0 0 1 3 0ZM12.75 16.5a1.5 1.5 0 0 1-3 0 1.5 1.5 0 0 1 3 0ZM17.25 14.25a1.5 1.5 0 0 1-3 0 1.5 1.5 0 0 1 3 0ZM21.75 12a1.5 1.5 0 0 1-3 0 1.5 1.5 0 0 1 3 0Z" />
  </svg>
);

export const RulerIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v1.244m-1.5 3.585V9.177m-1.5-3.585V4.348m-1.5 11.65v-1.243m16.5-11.65h-16.5A1.5 1.5 0 0 0 3 4.5v15a1.5 1.5 0 0 0 1.5 1.5h16.5a1.5 1.5 0 0 0 1.5-1.5v-15a1.5 1.5 0 0 0-1.5-1.5Zm-9 15h.008v.008H12v-.008Z" />
  </svg>
);

export const ShieldCheckIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
  </svg>
);

export const ShieldAlertIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m0-10.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285ZM12 15.75h.007v.008H12v-.008Z" />
  </svg>
);

export const DocumentTextIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
  </svg>
);

export const DocumentIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
  </svg>
);

export const EyeIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
  </svg>
);

export const EyeOffIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 0 0 1.934 12c.045.16.1.315.163.469C3.51 16.64 7.42 19.5 12 19.5c1.868 0 3.61-.472 5.143-1.303M17.657 17.657l-1.386-1.386M20.02 11.777c.045-.16.096-.32.152-.477C18.79 7.14 14.88 4.5 10 4.5c-1.442 0-2.812.272-4.07.767M10.88 10.88l-1.386-1.386m0 0L4.5 4.5m4.994 4.994l5.012 5.012M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
  </svg>
);

export const SunIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1.5M12 19.5V21M4.22 4.22l1.06 1.06M17.72 17.72l1.06 1.06M3 12h1.5M19.5 12H21M4.22 19.78l1.06-1.06M17.72 6.28l1.06-1.06M12 7.5a4.5 4.5 0 1 0 0 9 4.5 4.5 0 0 0 0-9Z" />
  </svg>
);

export const MoonIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.718 9.718 0 0 1 18 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 0 0 3 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 0 0 9.002-5.998Z" />
  </svg>
);

export const SparklesIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 21l-.813-5.096L3.096 15 8 14.187 8.813 9l.813 5.187L15 15l-5.187.904ZM18 10.5l-.36-.9L16.5 9.24l.9-.36.36-.9.36.9.9.36-.9.36-.36.9ZM19 4.5l-.2-.5-.5-.2.5-.2.2-.5.2.5.5.2-.5.2-.2.5Z" />
  </svg>
);

export const HourglassIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
  </svg>
);

export const MegaphoneIcon = ({ className = '', style = {} }) => (
  <svg className={className} style={getBaseStyle(style)} {...baseSvgProps}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M10.34 15.84c-.68-.68-1.5-1.2-2.4-1.54V10.7c.9-.34 1.72-.86 2.4-1.54L15 4v16l-4.66-4.16ZM3 9h3v6H3V9Zm15.5 3c0-1.8-1.04-3.36-2.5-4.12v8.24c1.46-.76 2.5-2.32 2.5-4.12ZM17 4.14v2.06c2.89.86 5 3.54 5 6.8s-2.11 5.94-5 6.8v2.06c4.01-.93 7-4.57 7-8.86s-2.99-7.93-7-8.86Z" />
  </svg>
);

