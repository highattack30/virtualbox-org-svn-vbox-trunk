# -*- coding: utf-8 -*-
# $Id$

"""
Test Manager WUI - Reports.
"""

__copyright__ = \
"""
Copyright (C) 2012-2015 Oracle Corporation

This file is part of VirtualBox Open Source Edition (OSE), as
available from http://www.virtualbox.org. This file is free software;
you can redistribute it and/or modify it under the terms of the GNU
General Public License (GPL) as published by the Free Software
Foundation, in version 2 as it comes in the "COPYING" file of the
VirtualBox OSE distribution. VirtualBox OSE is distributed in the
hope that it will be useful, but WITHOUT ANY WARRANTY of any kind.

The contents of this file may alternatively be used under the terms
of the Common Development and Distribution License Version 1.0
(CDDL) only, as it comes in the "COPYING.CDDL" file of the
VirtualBox OSE distribution, in which case the provisions of the
CDDL are applicable instead of those of the GPL.

You may elect to license modified versions of this file under the
terms and conditions of either the GPL or the CDDL or both.
"""
__version__ = "$Revision$"


# Validation Kit imports.
from common                             import webutils;
from testmanager.webui.wuicontentbase   import WuiContentBase, WuiTmLink, WuiSvnLinkWithTooltip;
from testmanager.webui.wuihlpgraph      import WuiHlpGraphDataTable, WuiHlpBarGraph;
from testmanager.webui.wuitestresult    import WuiTestSetLink;
from testmanager.webui.wuiadmintestcase import WuiTestCaseDetailsLink;
from testmanager.core.report            import ReportModelBase;


class WuiReportSummaryLink(WuiTmLink):
    """ Generic report summary link. """

    def __init__(self, sSubject, aIdSubjects, sName = WuiContentBase.ksShortReportLink,
                 tsNow = None, cPeriods = None, cHoursPerPeriod = None, fBracketed = False):
        from testmanager.webui.wuimain import WuiMain;
        dParams = {
            WuiMain.ksParamAction:                WuiMain.ksActionReportSummary,
            WuiMain.ksParamReportSubject:         sSubject,
            WuiMain.ksParamReportSubjectIds:      aIdSubjects,
        };
        if tsNow is not None:
            dParams[WuiMain.ksParamEffectiveDate] = tsNow;
        if cPeriods is not None:
            dParams[WuiMain.ksParamReportPeriods] = cPeriods;
        if cPeriods is not None:
            dParams[WuiMain.ksParamReportPeriodInHours] = cHoursPerPeriod;
        WuiTmLink.__init__(self, sName, WuiMain.ksScriptName, dParams, fBracketed = fBracketed);


class WuiReportBase(WuiContentBase):
    """
    Base class for the reports.
    """

    def __init__(self, oModel, dParams, fSubReport = False, fnDPrint = None, oDisp = None):
        WuiContentBase.__init__(self, fnDPrint = fnDPrint, oDisp = oDisp);
        self._oModel        = oModel;
        self._dParams       = dParams;
        self._fSubReport    = fSubReport;
        self._sTitle        = None;

    def generateNavigator(self, sWhere):
        """
        Generates the navigator (manipulate _dParams).
        Returns HTML.
        """
        assert sWhere == 'top' or sWhere == 'bottom';

        return '';

    def generateReportBody(self):
        """
        This is overridden by the child class to generate the report.
        Returns HTML.
        """
        return '<h3>Must override generateReportBody!</h3>';

    def show(self):
        """
        Generate the report.
        Returns (sTitle, HTML).
        """

        sTitle  = self._sTitle if self._sTitle is not None else type(self).__name__;
        sReport = self.generateReportBody();
        if not self._fSubReport:
            sReport = self.generateNavigator('top') + sReport + self.generateNavigator('bottom');
            sTitle = self._oModel.sSubject + ' - ' + sTitle; ## @todo add subject to title in a proper way!

        sReport += '\n\n<!-- HEYYOU: sSubject=%s aidSubjects=%s -->\n\n' % (self._oModel.sSubject, self._oModel.aidSubjects);
        return (sTitle, sReport);


class WuiReportSuccessRate(WuiReportBase):
    """
    Generates a report displaying the success rate over time.
    """

    def generateReportBody(self):
        self._sTitle = 'Success rate';

        adPeriods = self._oModel.getSuccessRates();

        sReport = '';

        oTable = WuiHlpGraphDataTable('Period', [ 'Succeeded', 'Skipped', 'Failed' ]);

        #for i in range(len(adPeriods) - 1, -1, -1):
        for i, dStatuses in enumerate(adPeriods):
            cSuccess  = dStatuses[ReportModelBase.ksTestStatus_Success] + dStatuses[ReportModelBase.ksTestStatus_Skipped];
            cTotal    = cSuccess + dStatuses[ReportModelBase.ksTestStatus_Failure];
            sPeriod   = self._oModel.getPeriodDesc(i);
            if cTotal > 0:
                iPctSuccess = dStatuses[ReportModelBase.ksTestStatus_Success] * 100 / cTotal;
                iPctSkipped = dStatuses[ReportModelBase.ksTestStatus_Skipped] * 100 / cTotal;
                iPctFailure = dStatuses[ReportModelBase.ksTestStatus_Failure] * 100 / cTotal;
                oTable.addRow(sPeriod, [ iPctSuccess, iPctSkipped, iPctFailure ],
                              [ '%s%% (%d)' % (iPctSuccess, dStatuses[ReportModelBase.ksTestStatus_Success]),
                                '%s%% (%d)' % (iPctSkipped, dStatuses[ReportModelBase.ksTestStatus_Skipped]),
                                '%s%% (%d)' % (iPctFailure, dStatuses[ReportModelBase.ksTestStatus_Failure]), ]);
            else:
                oTable.addRow(sPeriod, [ 0, 0, 0 ], [ '0%', '0%', '0%' ]);

        cTotalNow  = adPeriods[0][ReportModelBase.ksTestStatus_Success];
        cTotalNow += adPeriods[0][ReportModelBase.ksTestStatus_Skipped];
        cSuccessNow = cTotalNow;
        cTotalNow += adPeriods[0][ReportModelBase.ksTestStatus_Failure];
        sReport += '<p>Current success rate: ';
        if cTotalNow > 0:
            sReport += '%s%% (thereof %s%% skipped)</p>\n' \
                     % ( cSuccessNow * 100 / cTotalNow, adPeriods[0][ReportModelBase.ksTestStatus_Skipped] * 100 / cTotalNow);
        else:
            sReport += 'N/A</p>\n'

        oGraph = WuiHlpBarGraph('success-rate', oTable, self._oDisp);
        oGraph.setRangeMax(100);
        sReport += oGraph.renderGraph();

        return sReport;


class WuiReportFailuresBase(WuiReportBase):
    """
    Common parent of WuiReportFailureReasons and WuiReportTestCaseFailures.
    """

    def _splitSeriesIntoMultipleGraphs(self, aidSorted, cMaxSeriesPerGraph = 8):
        """
        Splits the ID array into one or more arrays, making sure we don't
        have too many series per graph.
        Returns array of ID arrays.
        """
        if len(aidSorted) <= cMaxSeriesPerGraph + 2:
            return [aidSorted,];
        cGraphs   = len(aidSorted) / cMaxSeriesPerGraph + (len(aidSorted) % cMaxSeriesPerGraph != 0);
        cPerGraph = len(aidSorted) / cGraphs + (len(aidSorted) % cGraphs != 0);

        aaoRet = [];
        cLeft  = len(aidSorted);
        iSrc   = 0;
        while cLeft > 0:
            cThis = cPerGraph;
            if cLeft <= cPerGraph + 2:
                cThis = cLeft;
            elif cLeft <= cPerGraph * 2 + 4:
                cThis = cLeft / 2;
            aaoRet.append(aidSorted[iSrc : iSrc + cThis]);
            iSrc  += cThis;
            cLeft -= cThis;
        return aaoRet;

    def _formatEdgeOccurenceSubject(self, oTransient):
        """
        Worker for _formatEdgeOccurence that child classes overrides to format
        their type of subject data in the best possible way.
        """
        _ = oTransient;
        assert False;
        return '';

    def _formatEdgeOccurence(self, oTransient):
        """
        Helper for formatting the transients.
        oTransient is of type ReportFailureReasonTransient or ReportTestCaseFailureTransient.
        """
        sHtml = u'<li>';
        if oTransient.fEnter:   sHtml += 'Since ';
        else:                   sHtml += 'Until ';
        sHtml += WuiSvnLinkWithTooltip(oTransient.iRevision, oTransient.sRepository, fBracketed = 'False').toHtml();
        sHtml += u', %s: ' % (WuiTestSetLink(oTransient.idTestSet, self.formatTsShort(oTransient.tsDone),
                                             fBracketed = False).toHtml(), )
        sHtml += self._formatEdgeOccurenceSubject(oTransient);
        sHtml += u'</li>\n';
        return sHtml;

    def _generateTransitionList(self, oSet):
        """
        Generates the enter and leave lists.
        """
        # Skip this if we're looking at builds.
        if self._oModel.sSubject in [self._oModel.ksSubBuild,] and len(self._oModel.aidSubjects) in [1, 2]:
            return u'';

        sHtml  = u'<h4>Movements:</h4>\n' \
                 u'<ul>\n';
        if len(oSet.aoEnterInfo) == 0 and len(oSet.aoLeaveInfo) == 0:
            sHtml += u'<li>No changes</li>\n';
        else:
            for oTransient in oSet.aoEnterInfo:
                sHtml += self._formatEdgeOccurence(oTransient);
            for oTransient in oSet.aoLeaveInfo:
                sHtml += self._formatEdgeOccurence(oTransient);
        sHtml += u'</ul>\n';

        return sHtml;


    def _formatSeriesNameForTable(self, oSet, idKey):
        """ Formats the series name for the HTML table. """
        _ = oSet;
        return '<td>%d</td>' % (idKey,);

    def _formatRowValueForTable(self, oRow, oPeriod, cColsPerSeries):
        """ Formats a row value for the HTML table. """
        _ = oPeriod;
        if oRow is None:
            return u'<td colspan="%d"> </td>' % (cColsPerSeries,);
        if cColsPerSeries == 2:
            return u'<td align="right">%u%%</td><td align="center">%u / %u</td>' \
                   % (oRow.cHits * 100 / oRow.cTotal, oRow.cHits, oRow.cTotal);
        return u'<td align="center">%u</td>' % (oRow.cHits,);

    def _formatSeriesTotalForTable(self, oSet, idKey, cColsPerSeries):
        """ Formats the totals cell for a data series in the HTML table. """
        dcTotalPerId = getattr(oSet, 'dcTotalPerId', None);
        if cColsPerSeries == 2:
            return u'<td align="right">%u%%</td><td align="center">%u/%u</td>' \
                   % (oSet.dcHitsPerId[idKey] * 100 / dcTotalPerId[idKey], oSet.dcHitsPerId[idKey], dcTotalPerId[idKey]);
        return u'<td align="center">%u</td>' % (oSet.dcHitsPerId[idKey],);

    def _generateTableForSet(self, oSet, sColumnName, aidSorted = None, fWithTotals = True, cColsPerSeries = None):
        """
        Turns the set into a table.

        Returns raw html.
        """
        sHtml  = u'<table class="tmtbl-report-set" width="100%%">\n';
        if cColsPerSeries is None:
            cColsPerSeries = 2 if hasattr(oSet, 'dcTotalPerId') else 1;

        # Header row.
        sHtml += u' <tr><thead><th></th><th>%s</th>' % (webutils.escapeElem(sColumnName),)
        for oPeriod in reversed(oSet.aoPeriods):
            sHtml += u'<th colspan="%d">%s</th>' % (cColsPerSeries, webutils.escapeElem(oPeriod.sDesc),);
        if fWithTotals:
            sHtml += u'<th colspan="%d">Total</th>' % (cColsPerSeries,);
        sHtml += u'</thead></td>\n';

        # Each data series.
        if aidSorted is None:
            aidSorted = oSet.dSubjects.keys();
        sHtml += u' <tbody>\n';
        for iRow, idKey in enumerate(aidSorted):
            sHtml += u'  <tr class="%s">' % ('tmodd' if iRow & 1 else 'tmeven',);
            sHtml += u'<td align="left">#%u</td>' % (iRow + 1,);
            sHtml += self._formatSeriesNameForTable(oSet, idKey);
            for oPeriod in reversed(oSet.aoPeriods):
                oRow = oPeriod.dRowsById.get(idKey, None);
                sHtml += self._formatRowValueForTable(oRow, oPeriod, cColsPerSeries);
            if fWithTotals:
                sHtml += self._formatSeriesTotalForTable(oSet, idKey, cColsPerSeries);
            sHtml += u' </tr>\n';
        sHtml += u' </tbody>\n';
        sHtml += u'</table>\n';
        return sHtml;




class WuiReportFailureReasons(WuiReportFailuresBase):
    """
    Generates a report displaying the failure reasons over time.
    """

    def _formatEdgeOccurenceSubject(self, oTransient):
        return u'%s / %s' % ( webutils.escapeElem(oTransient.oReason.oCategory.sShort),
                              webutils.escapeElem(oTransient.oReason.sShort),);

    def _formatSeriesNameForTable(self, oSet, idKey):
        oReason = oSet.dSubjects[idKey];
        sHtml  = '<td>'
        sHtml += u'%s / %s' % ( webutils.escapeElem(oReason.oCategory.sShort), webutils.escapeElem(oReason.sShort),);
        sHtml += '</td>'
        return sHtml;


    def generateReportBody(self):
        self._sTitle = 'Failure reasons';

        #
        # Get the data and sort the data series in descending order of badness.
        #
        oSet = self._oModel.getFailureReasons();
        aidSorted = sorted(oSet.dSubjects, key = lambda idReason: oSet.dcHitsPerId[idReason], reverse = True);

        #
        # Generate table and transition list. These are the most useful ones with the current graph machinery.
        #
        sHtml  = self._generateTableForSet(oSet, 'Test Cases', aidSorted);
        sHtml += self._generateTransitionList(oSet);

        #
        # Check if most of the stuff is without any assign reason, if so, skip
        # that part of the graph so it doesn't offset the interesting bits.
        #
        fIncludeWithoutReason = True;
        for oPeriod in reversed(oSet.aoPeriods):
            if oPeriod.cWithoutReason > oSet.cMaxHits * 4:
                fIncludeWithoutReason = False;
                sHtml += '<p>Warning: Many failures without assigned reason!</p>\n';
                break;

        #
        # Generate the graph.
        #
        fGenerateGraph = len(aidSortedRaw) <= 9 && len(aidSortedRaw) > 0; ## Make this configurable.
        if fGenerateGraph:
            asNames = [];
            for idReason in aidSorted:
                oReason = oSet.dSubjects[idReason];
                asNames.append('%s / %s' % (oReason.oCategory.sShort, oReason.sShort,) )
            if fIncludeWithoutReason:
                asNames.append('No reason');

            oTable = WuiHlpGraphDataTable('Period', asNames);

            cMax = oSet.cMaxHits;
            for _, oPeriod in enumerate(reversed(oSet.aoPeriods)):
                aiValues = [];

                for idReason in aidSorted:
                    oRow = oPeriod.dRowsById.get(idReason, None);
                    iValue = oRow.cHits if oRow is not None else 0;
                    aiValues.append(iValue);

                if fIncludeWithoutReason:
                    aiValues.append(oPeriod.cWithoutReason);
                    if oPeriod.cWithoutReason > cMax:
                        cMax = oPeriod.cWithoutReason;

                oTable.addRow(oPeriod.sDesc, aiValues);

            oGraph = WuiHlpBarGraph('failure-reason', oTable, self._oDisp);
            oGraph.setRangeMax(max(cMax + 1, 3));
            sHtml += oGraph.renderGraph();
        return sHtml;


class WuiReportTestCaseFailures(WuiReportFailuresBase):
    """
    Generates a report displaying the failure reasons over time.
    """

    def _formatEdgeOccurenceSubject(self, oTransient):
        sHtml = u'%s ' % ( webutils.escapeElem(oTransient.oTestCase.sName),);
        sHtml += WuiTestCaseDetailsLink(oTransient.oTestCase.idTestCase, fBracketed = False).toHtml();
        return sHtml;

    def _formatSeriesNameForTable(self, oSet, idKey):
        oTestCase = oSet.dSubjects[idKey];
        sHtml  = '<td>'
        sHtml += WuiReportSummaryLink(ReportModelBase.ksSubTestCase, oTestCase.idTestCase, sName = oTestCase.sName).toHtml();
        sHtml += u' ';
        sHtml += WuiTestCaseDetailsLink(oTestCase.idTestCase).toHtml();
        sHtml += '</td>'
        return sHtml;

    def generateReportBody(self):
        self._sTitle = 'Test Case Failures';


        #
        # Get the data and sort the data series in descending order of badness.
        #
        oSet = self._oModel.getTestCaseFailures();
        if self._oModel.tsNow is not None and False:
            # Sort the total.
            aidSortedRaw = sorted(oSet.dSubjects,
                                  key = lambda idKey: oSet.dcHitsPerId[idKey] * 10000 / oSet.dcTotalPerId[idKey],
                                  reverse = True);
        else:
            # Sort by NOW column.
            dTmp = {};
            for idKey in oSet.dSubjects:
                oRow = oSet.aoPeriods[-1].dRowsById.get(idKey, None);
                if oRow is None:    dTmp[idKey] = 0;
                else:               dTmp[idKey] = oRow.cHits * 10000 / max(1, oRow.cTotal);
            aidSortedRaw = sorted(dTmp, key = lambda idKey: dTmp[idKey], reverse = True);

        #
        # Generate table and transition list. These are the most useful ones with the current graph machinery.
        #
        sHtml  = self._generateTableForSet(oSet, 'Test Cases', aidSortedRaw);
        sHtml += self._generateTransitionList(oSet);

        #
        # Generate the graph.
        #
        fGenerateGraph = len(aidSortedRaw) <= 6 && len(aidSortedRaw) > 0; ## Make this configurable.
        if fGenerateGraph:
            # Figure the graph width for all of them.
            uPctMax = max(oSet.uMaxPct, oSet.cMaxHits * 100 / oSet.cMaxTotal);
            uPctMax = max(uPctMax + 2, 10);

            for _, aidSorted in enumerate(self._splitSeriesIntoMultipleGraphs(aidSortedRaw, 8)):
                asNames = [];
                for idKey in aidSorted:
                    oSubject = oSet.dSubjects[idKey];
                    asNames.append(oSubject.sName);

                oTable = WuiHlpGraphDataTable('Period', asNames);

                for _, oPeriod in enumerate(reversed(oSet.aoPeriods)):
                    aiValues = [];
                    asValues = [];

                    for idKey in aidSorted:
                        oRow = oPeriod.dRowsById.get(idKey, None);
                        if oRow is not None:
                            uPct = oRow.cHits * 100 / oRow.cTotal;
                            aiValues.append(uPct);
                            asValues.append('%u%% (%u/%u)' % (uPct, oRow.cHits, oRow.cTotal));
                        else:
                            aiValues.append(0);
                            asValues.append('0');

                    oTable.addRow(oPeriod.sDesc, aiValues, asValues);

                if True: # pylint: disable=W0125
                    aiValues = [];
                    asValues = [];
                    for idKey in aidSorted:
                        uPct = oSet.dcHitsPerId[idKey] * 100 / oSet.dcTotalPerId[idKey];
                        aiValues.append(uPct);
                        asValues.append('%u%% (%u/%u)' % (uPct, oSet.dcHitsPerId[idKey], oSet.dcTotalPerId[idKey]));
                    oTable.addRow('Totals', aiValues, asValues);

                oGraph = WuiHlpBarGraph('testcase-failures', oTable, self._oDisp);
                oGraph.setRangeMax(uPctMax);
                sHtml += '<br>\n';
                sHtml += oGraph.renderGraph();

        return sHtml;


class WuiReportSummary(WuiReportBase):
    """
    Summary report.
    """

    def generateReportBody(self):
        self._sTitle = 'Summary';
        sHtml = '<p>This will display several reports and listings useful to get an overview of %s (id=%s).</p>' \
             % (self._oModel.sSubject, self._oModel.aidSubjects,);

        oSuccessRate      = WuiReportSuccessRate(     self._oModel, self._dParams, fSubReport = True,
                                                      fnDPrint = self._fnDPrint, oDisp = self._oDisp);
        oTestCaseFailures = WuiReportTestCaseFailures(self._oModel, self._dParams, fSubReport = True,
                                                      fnDPrint = self._fnDPrint, oDisp = self._oDisp);
        oFailureReasons   = WuiReportFailureReasons(  self._oModel, self._dParams, fSubReport = True,
                                                      fnDPrint = self._fnDPrint, oDisp = self._oDisp);
        for oReport in [oSuccessRate, oTestCaseFailures, oFailureReasons, ]:
            (sTitle, sContent) = oReport.show();
            sHtml += '<br>'; # drop this layout hack
            sHtml += '<div>';
            sHtml += '<h3>%s</h3>\n' % (webutils.escapeElem(sTitle),);
            sHtml += sContent;
            sHtml += '</div>';

        return sHtml;

