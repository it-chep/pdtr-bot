from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Sequence, TypedDict, Any

import xlrd
from abc import ABC, abstractmethod
from io import BytesIO
from openpyxl import Workbook

from agora.core.utils.xls_parser.dto import ParsingErrorDTO, ParsingResultErrorDTO, ParsingResultSuccessDTO
from agora.core.utils.xls_parser.exceptions import MapperErrorsException, BaseSaveError
from agora.core.utils.xls_parser.error_enum import XlsParserErrorEnum

if TYPE_CHECKING:
    from xlrd.sheet import Sheet
    from xlrd.book import Book
    from agora.core.utils.xls_parser.mapper import XlsMapper


class BaseXlsParser(ABC):
    dto_type: Optional[TypedDict] = None
    max_line_count: int = 1000
    sheet_name: str = None
    debug_errors: bool = False

    def _parse_xls(
        self, xls_file_path: Optional[str] = None, xls_file_content: Optional[Any] = None
    ) -> tuple[Book, Sheet]:
        """Чтение excel файла"""
        workbook: Book = xlrd.open_workbook(filename=xls_file_path, file_contents=xls_file_content, on_demand=True)
        if self.sheet_name:
            worksheet = workbook.sheet_by_name(self.sheet_name)
        else:
            worksheet = workbook.sheet_by_index(0)
        return workbook, worksheet

    def _debug(self, text: str) -> None:
        """Дебаг"""
        if self.debug_errors:
            print(text)

    def _response_error(self, error_dto: ParsingResultErrorDTO) -> ParsingResultErrorDTO | None:
        """Показ или возрат ошибок"""
        if self.debug_errors:
            print("[ERROR LOADING]. Пожалуйста загрузите корректный файл")
            print(f"Количесто строк Excel: {error_dto['lines']}")
            print("Ошибки:")
            for error in error_dto["errors"]:
                print(f"Строка: {error['line']}. Колонка: {error['column']}. Ошибка: {error['error'].title()}")
            return
        return error_dto

    def _response_success(self, success_dto: ParsingResultSuccessDTO) -> ParsingResultSuccessDTO | None:
        """Показ или возрат успешного выполнения"""
        if self.debug_errors:
            print("[SUCCESS LOADING]. Загрузка успешно выполнена")
            print(f"Количесто строк Excel: {success_dto['lines']}")
            return
        return success_dto

    def _clean_items(self, data: dict, line: int) -> Any:
        """Сборка dto из данных"""
        return self.mapper.to_dict(data, line, self.dto_type)

    def _validate_columns(self, columns: list) -> None:
        """Валидация колонок"""
        self.mapper.validate_columns(columns)

    def _get_col_names(self) -> list[str]:
        """Получить колонки"""
        return self.mapper.get_col_names()

    def _error(
        self, errors: list | str, line_count: int = 0, items: Optional[list] = None
    ) -> tuple[bool, ParsingResultErrorDTO]:
        """Отдача ошибки"""
        return False, self._response_error(
            ParsingResultErrorDTO(
                lines=line_count,
                items=items or list(),
                errors=errors if type(errors) is list else [ParsingErrorDTO(line=None, column=None, error=errors)],
            )
        )

    def generate_layout(self) -> BytesIO:
        """Генерация шаблона с полями"""
        workbook = Workbook()
        output = BytesIO()
        sheet = workbook.active
        for col_num, name in enumerate(self._get_col_names()):
            sheet.cell(row=1, column=col_num + 1, value=name)
        workbook.save(output)
        output.seek(0)
        return output

    def upload(
        self,
        xls_file_path: Optional[str] = None,
        xls_file_content: Optional[Any] = None,
        save_kwargs: Optional[dict] = None,
        sheet_name: Optional[str] = None,
        debug_errors: bool = False,
    ) -> tuple[bool, ParsingResultSuccessDTO | ParsingResultErrorDTO | None]:
        """Определяем параметры"""
        self.sheet_name = sheet_name
        self.debug_errors = debug_errors

        """Загрузка файла и обработка"""
        self._debug("Загрузка файла...")
        try:
            workbook, worksheet = self._parse_xls(xls_file_path, xls_file_content)
        except Exception as exception:
            return self._error(XlsParserErrorEnum.LOAD_FILE_ERROR + str(exception))
        line_count: int = worksheet.nrows
        self._debug("Файл загружен")

        if line_count > self.max_line_count + 1:
            """Проверка на количество строк"""
            return self._error(
                XlsParserErrorEnum.MAX_LINE_COUNT_ERROR + str(self.max_line_count), line_count=line_count
            )

        columns: list[str] = list()
        items: list[Any] = list()
        row_index: int = 0
        errors: list[ParsingErrorDTO] = list()

        self._debug("Обработка данных файла...")

        while row_index < line_count:
            column_index: int = 0
            _data: dict = dict()

            while column_index < worksheet.ncols:
                cell_value: str = str(worksheet.cell_value(row_index, column_index))
                if row_index == 0:
                    """Если первая строчка - добавляем в раздел колонки"""
                    columns.append(cell_value.strip())
                else:
                    """Строчки номер > 1 - строчки с данными"""
                    _data.update({columns[column_index]: cell_value.strip()})
                column_index += 1

            if _data:
                cleaned_data: Optional[TypedDict] = None

                """Проверяем корректность строчки, если есть ошибки добавляем их в список ошибок"""
                try:
                    cleaned_data = self._clean_items(_data, line=row_index)
                except MapperErrorsException as exception:
                    errors.extend(exception.errors)

                if cleaned_data:
                    processed_data: Any | None = None
                    try:
                        processed_data = self.process_row(cleaned_data)
                    except Exception as exception:
                        errors.append(
                            ParsingErrorDTO(
                                line=row_index, column=None, error=XlsParserErrorEnum.PROCESS_ROW_ERROR + str(exception)
                            )
                        )

                    if processed_data and processed_data not in items:
                        items.append(processed_data)
            else:
                """Валидация колонок на наличие обязательных"""
                try:
                    self._validate_columns(columns)
                except MapperErrorsException as exception:
                    return self._error(exception.errors, line_count=line_count, items=items)

            row_index += 1

        workbook.release_resources()

        if row_index == 1:
            """Если пустой файл"""
            return self._error(XlsParserErrorEnum.DATA_EMPTY, line_count=line_count, items=items)

        self._debug("Файл обработан")

        if errors:
            """Если есть ошибки валидации отдаем ошибки"""
            return self._error(errors, line_count=line_count, items=items)

        self._debug("Сохранение...")
        save_response: Any = None
        try:
            """Запуска сохранение"""
            save_response = self.save(items, **(save_kwargs or dict()))
        except BaseSaveError as exception:
            return self._error(exception.message, line_count=line_count, items=items)
        except Exception as exception:
            return self._error(XlsParserErrorEnum.SAVE_ERROR + str(exception), line_count=line_count, items=items)
        self._debug("Сохранение выполнено")

        if hasattr(self, "post_event"):
            """Запуск post_event метода, если он есть"""
            self._debug("Запуск Postevent...")
            try:
                getattr(self, "post_event")(items)
            except Exception as exception:
                return self._error(
                    XlsParserErrorEnum.POST_EVENT_ERROR + str(exception), line_count=line_count, items=items
                )
            self._debug("Postevent выполнен")

        success_dto: ParsingResultSuccessDTO = ParsingResultSuccessDTO(
            items=items, lines=line_count, save_response=save_response
        )
        return True, self._response_success(success_dto)

    @abstractmethod
    def process_row(self, data: Any) -> Any:
        """Обработка данных"""
        ...

    @property
    @abstractmethod
    def mapper(self) -> XlsMapper:
        """Маппинг полей"""
        ...

    @abstractmethod
    def save(self, items: Sequence[TypedDict], *args, **kwargs) -> None:
        """Сохранение объектов"""
        ...
