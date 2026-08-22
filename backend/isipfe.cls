%========= File containing the ISIPFE LaTeX Class =========%
% Corrected version for Overleaf 2024/2026                  %
% Corrections :                                             %
%   1. Option "pfe" déclarée                               %
%   2. \usepackage → \RequirePackage partout               %
%   3. Package enumitem ajouté (requis par acronyms)       %
%   4. minitoc sans option de langue (conflit babel)       %
%==========================================================%

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{isipfe}[2024/05/01 ISI PFE LaTeX Class Corrected]

\RequirePackage{ifthen}

%================ Options ================%
\newboolean{isBinomal}
\setboolean{isBinomal}{false}
\DeclareOption{isBinomal}{\setboolean{isBinomal}{true}}

\newboolean{wantToTypeCompanyAddress}
\setboolean{wantToTypeCompanyAddress}{false}
\DeclareOption{wantToTypeCompanyAddress}{\setboolean{wantToTypeCompanyAddress}{true}}

% CORRECTION 1 : Option "pfe" déclarée (était inconnue → crash immédiat)
\DeclareOption{pfe}{}

% Passer les options inconnues à la classe de base
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{book}}

\ProcessOptions\relax

\LoadClass[12pt,a4paper,oneside]{book}

%================ Géométrie des pages ================%
\RequirePackage[a4paper]{geometry}
\geometry{
    top=25mm,
    bottom=25mm,
    left=22mm,
    right=22mm,
    headheight=15pt,
    headsep=10mm,
    footskip=15mm
}

\brokenpenalty=10000
\renewcommand\floatpagefraction{0.8}

%================ Césures ================%
% CORRECTION 2 : \usepackage → \RequirePackage
\RequirePackage[none]{hyphenat}

%================ Espacement des titres ================%
% CORRECTION 2 : \usepackage → \RequirePackage
\RequirePackage{titlesec}
\titlespacing*{\section}{7mm}{12pt}{8pt}
\titlespacing*{\subsection}{15mm}{12pt}{8pt}
\titlespacing*{\subsubsection}{18mm}{12pt}{6pt}

%================ Interligne et indentation ================%
% CORRECTION 2 : \usepackage → \RequirePackage
\RequirePackage{setspace}
\setstretch{1.5}
\setlength{\parindent}{12mm}

%================ En-têtes et pieds de page ================%
\RequirePackage{fancyhdr}
\RequirePackage{xspace}

%================ Langues ================%
\RequirePackage[utf8]{inputenc}
\RequirePackage[T1]{fontenc}
\RequirePackage[english,french]{babel}
\RequirePackage{csquotes}

%================ Bibliographie ================%
%\RequirePackage[
    %backend=bibtex,
    %style=ieee,
    %sorting=none
%]{biblatex}
\RequirePackage[numbers,sort&compress]{natbib}
%================ Couleurs ================%
% CORRECTION 2 : \usepackage → \RequirePackage
\RequirePackage[table]{xcolor}
\definecolor{isiBlue}{RGB}{31, 78, 121}

%================ Liste des Acronymes (DataTool) ================%
% CORRECTION 2 : \usepackage → \RequirePackage
\RequirePackage{datatool}
%\RequirePackage{acronym}

% CORRECTION 3 : enumitem ajouté (requis par \begin{itemize}[label={}])
\RequirePackage{enumitem}

\newcommand{\sortitem}[2][\relax]{%
  \DTLnewrow{list}%
  \DTLnewdbentry{list}{sortlabel}{#1}%
  \DTLnewdbentry{list}{description}{%
      \begin{minipage}[t]{0.15\columnwidth}\textbf{#1}\end{minipage}%
      \begin{minipage}[t]{0.05\columnwidth}\textbf{=}\end{minipage}%
      \begin{minipage}[t]{0.75\columnwidth}#2\end{minipage}%
  }%
}

\newenvironment{acronyms}{%
  \DTLifdbexists{list}{\DTLcleardb{list}}{\DTLnewdb{list}}%
}{%
  \DTLsort{sortlabel}{list}%
  \begin{itemize}[label={}]%
    \DTLforeach*{list}{\theDesc=description}{\item \theDesc}%
  \end{itemize}%
}

%================ Mini tables des matières ================%
% CORRECTION 4 : suppression de l'option [french] → conflit avec babel
\RequirePackage{minitoc}
\mtcsettitle{minitoc}{Plan}
\setcounter{minitocdepth}{1}

%================ Style des chapitres ================%
\makeatletter
\def\thickhrulefill{\leavevmode \leaders \hrule height 1.2ex \hfill \kern \z@}
\def\@makechapterhead#1{%
  \vspace*{20\p@}%
  {\parindent \z@ \centering \reset@font
        \thickhrulefill\quad
        \scshape\bfseries\@chapapp{} \thechapter
        \quad \thickhrulefill
        \par\nobreak\vspace*{10\p@}\hrule\vspace*{10\p@}%
        \Huge \bfseries #1 \par\nobreak
        \vspace*{10\p@}\hrule\vskip 40\p@
  }
}
\makeatother

%================ Légendes (figures et tableaux) ================%
% CORRECTION 2 : \usepackage → \RequirePackage
\RequirePackage{caption}
\captionsetup[table]{labelfont=bf, name=Tableau, labelsep=colon, skip=10pt}
\captionsetup[figure]{labelfont=bf, name=Figure, labelsep=colon, skip=10pt}

%================ Styles fancyhdr ================%
\pagestyle{fancy}
\fancyhf{}
\lhead{\nouppercase{\leftmark}}
\rfoot{\thepage}
\renewcommand{\headrulewidth}{0.3pt}
\renewcommand{\footrulewidth}{0.3pt}

\fancypagestyle{frontmatter}{%
  \fancyhf{}%
  \fancyfoot[R]{\thepage}%
  \renewcommand{\headrulewidth}{0pt}%
}

\fancypagestyle{backcover}{%
  \fancyhf{}%
  \fancyfoot[C]{\small\color{isiBlue} Institut Supérieur d'Informatique}%
}

%================ Graphiques et flottants ================%
% CORRECTION 2 : \usepackage → \RequirePackage
\RequirePackage{graphicx}
\RequirePackage{float}